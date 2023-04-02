import eeny

tree = eeny.read_tree("rule110.eeny")
tree = eeny.preprocess(tree)

eeny.execute(tree)