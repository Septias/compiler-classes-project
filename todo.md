
- The clean fix would be to merge the two parser cases into a single EDictAccess/subscript node and let the type checker split them based on type. But that's a bigger refactor touching all the downstream passes that currently match ETupleAccess.
