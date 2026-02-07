"""
Tree Edit Distance Algorithm

Calculates the structural difference between two DOM trees.
Used to compare a test page's structure with a known brand's structure.
"""


def tree_edit_distance(t1: dict, t2: dict) -> int:
    """
    Calculate the tree edit distance between two DOM trees.
    
    Args:
        t1: First DOM tree (dict with 'tag' and 'children')
        t2: Second DOM tree (dict with 'tag' and 'children')
    
    Returns:
        int: Edit distance (lower = more similar)
    """
    if t1["tag"] != t2["tag"]:
        cost = 1
    else:
        cost = 0
    
    c1 = t1.get("children", [])
    c2 = t2.get("children", [])
    total = abs(len(c1) - len(c2))
    
    for child1, child2 in zip(c1, c2):
        total += tree_edit_distance(child1, child2)
    
    return cost + total