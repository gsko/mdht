"""
@author Greg Skoczek

Implementation of a RoutingTable for the Kademlia network
@see references/kademlia.pdf section 2.4
@see references/README for the DHT BEP005
@see references/subsecond.pdf
@see references/README for Rasterbar's BitTorrent Overview

"""
import random
from collections import defaultdict

from twisted.python import log
from zope.interface import Interface, implements

from mdht import contact, constants
from mdht.kademlia import kbucket

class IRoutingTable(Interface):
    """
    A routing table as described in the paper on kademlia

    @see DHBot/references/kademlia.pdf

    """
    def offer_node(self, node):
        """Offers the given node to the RoutingTable

        The node may not be accepted, if for example it is stale
        @return boolean indicating if the node was accepted or not.
        If the node is already found in the RoutingTable, True should
        be returned

        """

    def remove_node(self, node):
        """Remove the given node from the tree

        @return boolean indicating whether the node was found

        """

    def get_node(self, node_id):
        """
        Returns the node with the given node_id (if found)

        @return a contact.Node or None

        """

    def get_node_by_address(self, address):
        """
        Returns the node operating behind the given address (ip/port)

        @returns a set of contact.Node's that are operating on and
            sharing the given address if there are any. If there
            are no recorded nodes operating on this address,
            None is returned

        """

    def get_closest_nodes(self, node_id, num_nodes=constants.k):
        """
        Retrieves the `num_nodes' nodes closest to `node_id'

        @return an iterable containing the nodes

        """

class TreeRoutingTable(object):
    """
    Prefix tree based Kademlia routing table

    This implementation follows the standard kademlia routing table
    design with some improvements noted in the subsecond.pdf paper
    (see the references in the module docstring, above)

    """

    implements(IRoutingTable)

    def __init__(self, node_id):
        self.node_id = node_id
        k = kbucket.KBucket(0, 2**constants.id_size)
        self.root = _TreeNode(k)
        self.nodes_dict = {}
        self.nodes_by_addr = defaultdict(set)
        self.active_kbuckets = [k]

    def offer_node(self, node):
        # If node isn't in the routing table,
        # try adding it
        if node.node_id in self.nodes_dict:
            return True
        else:
            # Try to recursively add node to our tree (rooted at self.root)
            node_accepted = self._offer_node(self.root, node)
            if node_accepted:
                # Add the node into two local dictionaries
                # for quick lookup later
                self.nodes_dict[node.node_id] = node
                self.nodes_by_addr[node.address].add(node)
            return node_accepted

    def remove_node(self, node):
        if node.node_id in self.nodes_dict:
            del self.nodes_dict[node.node_id]
            self.nodes_by_addr[node.address].remove(node)
            if len(self.nodes_by_addr[node.address]) == 0:
                del self.nodes_by_addr[node.address]
            self._remove_node(self.root, node)
            return True
        else:
            return False

    def get_node(self, node_id):
        if node_id in self.nodes_dict:
            return self.nodes_dict[node_id]

    def get_node_by_address(self, address):
        if address in self.nodes_by_addr:
            nodes_set = self.nodes_by_addr[address]
            if len(nodes_set) > 0:
                return nodes_set

    def get_closest_nodes(self, node_id, num_nodes=constants.k):
        closest_nodes = []
        self._get_closest_nodes(node_id, self.root, closest_nodes, num_nodes)

        closest_nodes.sort(key = lambda node: node.distance(node_id))
        return closest_nodes[:num_nodes]

    def get_kbuckets(self):
        """
        Return all the active kbuckets in this tree

        @see mdht.kademlia.kbucket.KBucket
        @return an iterable containing kbuckets that have nodes in them

        """
        return self.active_kbuckets

    def _offer_node(self, tnode, node):
        """
        Recursive helper function for offer_node
        
        @return boolean indicating whether node was added
        to tnode or its subtree

        """
        # Either the treenode is invalid or the given
        # node's id would not fit into this treenodes kbucket
        #
        # Don't process any further
        if (tnode is None) or not (tnode.kbucket.key_in_range(node.node_id)):
            return False

        # Try pushing the node into the left or right subtree
        node_accepted = (self._offer_node(tnode.lchild, node) or
                         self._offer_node(tnode.rchild, node))
        if node_accepted:
            return True

        # Try to insert the node into this treenode's kbucket
        # if this treenode is a leaf
        if tnode.is_leaf():
            node_accepted = tnode.kbucket.offer_node(node)
            if node_accepted:
                return True
            # If the kbucket rejected the node, it is probably
            # full. Check to see if we can split the kbucket
            # and insert the node into one of its children
            if (tnode.kbucket.full() and
                tnode.kbucket.splittable() and
                tnode.kbucket.key_in_range(self.node_id)):
                self._split(tnode)
                node_accepted = self._offer_node(tnode, node)
                return node_accepted
        return False

    def _remove_node(self, tnode, node):
        """Recursive helper function for remove_node"""
        if tnode and tnode.kbucket.key_in_range(node.node_id):
            # Recurse down into the treenode which contains the given node
            self._remove_node(tnode.lchild, node)
            self._remove_node(tnode.rchild, node)

            # We have found our kbucket
            if tnode.is_leaf():
                tnode.kbucket.remove_node(node)

    def _get_closest_nodes(self, node_id, tnode, closest_nodes, num_nodes):
        """
        Recursive helper function for get_closest_nodes

        @param node_id: We are looking for nodes closest to this ID
        @param tnode: We are recursing down tnode and its subtrees
        @param closest_nodes: The list where we are storing our results
        @param num_nodes: How many nodes we are looking for
        
        @returns None

        """
        # If we have collected more nodes than we need,
        # stop searching
        if len(closest_nodes) >= num_nodes:
            return
        if tnode.is_leaf():
            bucket_nodes = tnode.kbucket.get_nodes()
            closest_nodes.extend(bucket_nodes)
            return
        if tnode.lchild.kbucket.key_in_range(node_id):
            direction = "left"
            self._get_closest_nodes(
                    node_id, tnode.lchild, closest_nodes, num_nodes)
        elif tnode.rchild.kbucket.key_in_range(node_id):
            direction = "right"
            self._get_closest_nodes(
                    node_id, tnode.rchild, closest_nodes, num_nodes)
        else:
            # This else should never be reached
            log.msg("RoutingTable: node_id didn't fall into either"
                    " of a treenode's children. ???")
            return

        # If trying the left/right subtree did not yield
        # enough nodes, try going down the other subtree
        if direction == "left":
            self._get_closest_nodes(
                    node_id, tnode.rchild, closest_nodes, num_nodes)
        elif direction == "right":
            self._get_closest_nodes(
                    node_id, tnode.lchild, closest_nodes, num_nodes)
        return

    def _split(self, tnode):
        """
        Split the given node into two children nodes

        You can only split a treenode that does not already
        have children (ie, is_leaf())

        After the split, the KBucket found in this treenode
        will be empty and have a maxsize of 0

        The lchild and rchild attributes will contain references
        to the two newly created treenodes

        @return boolean indicating whether the split operation
            was succesful

        """
        if (not tnode.is_leaf() or
            not tnode.kbucket.splittable() or
            not tnode.kbucket.key_in_range(self.node_id)):
            return False

        (lbucket, rbucket) = tnode.kbucket.split()
        tnode.lchild = _TreeNode(lbucket)
        tnode.rchild = _TreeNode(rbucket)
        # The original kbucket is no longer active
        # (its ranges will be used in guiding the recursion
        # process, but it will not store nodes)
        self.active_kbuckets.remove(tnode.kbucket)
        self.active_kbuckets.extend([lbucket, rbucket])
        return True

class _TreeNode(object):
    """
    An auxilary node structure for the TreeRoutingTable
    
    A treenode contains a kbucket and two children treenodes
    (kbucket, lchild, and rchild respectively)

    """
    def __init__(self, kbucket):
        self.kbucket = kbucket
        self.lchild = None
        self.rchild = None

    def is_leaf(self):
        """Tells whether this TreeNode is a leaf"""
        return (self.lchild, self.rchild) == (None, None)


class SubsecondRoutingTable(TreeRoutingTable):
    def __init__(self, node_id):
        TreeRoutingTable.__init__(self, node_id)
        self.other_bucket_count = 0

    def _split(self, tnode):
        """
        An optimization of the TreeRoutingTable split function


        This function extends the TreeRoutingTable.split method
        to modify the size of the created KBuckets (as an 
        optimization found in section 5.D of references/subsecond.pdf

        @see TreeRoutingTable.split
        @see references/subsecond.pdf

        """
        valid_split = TreeRoutingTable._split(self, tnode)
        if valid_split:
            lbucket = tnode.lchild.kbucket
            rbucket = tnode.rchild.kbucket
            if lbucket.key_in_range(self.node_id):
                rbucket.maxsize = self._newbucketsize()
            else:
                lbucket.maxsize = self._newbucketsize()
        self.other_bucket_count += 1
        return valid_split

    def _newbucketsize(self):
        """
        Determine the optimal size of a new KBucket

        The first KBucket will have size 128, the following
        KBuckets will have sizes of 64, 32, 16, and all the
        remaining KBuckets will have size 8.

        @see references/subsecond.pdf

        """
        return max(128 / 2 ** self.other_bucket_count, constants.k)

