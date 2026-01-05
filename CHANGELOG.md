## Extended the type checker to check Classes
### AST
* add expressions EField for field access and EMethod for method calls to the AST
* add Statement SClass for class definitions to the AST
* change SAssign to also take EField (ast_1) and ETupleAccess (ast_2_shrunk, ast_3_revealed) as value of lhs (this is needed to be able to reassign to membervariables of dataclass objects)
* make pretty printing compatible with extended AST

### parsing
* add parsing context to keep track of defined classes
* change how assignments are parsed to allow assignments to member variables
* add parsing of classes
* change type node mapping to accomodate classes
* change structure of Program to allow easy handling of classes in later steps

### shrinking
* add functionality to shrink class definitions
* change shrinking of assignments to allow for membervariable assigns
* add functionality to shrink Efield and EMethod expressions

### uniquify
* change assignment to convert member variable assignment to tuple access

### reveal functions
* make assignments compatible with the rest of the changes

### convert assignments
* add functionality to be able to treat tuples and dataclass objects the same in later passes

### interpreter
* add VClass and VObject to model classes
* add functionality for constructors and methods in apply_fun
* add fields and objects logic for interpretation
* interpret class definitions 

### type checker
* now also annotates the type of member variables inside of methods
* expanded type equality check to handle inheritance correctly
* type check member variable assignment
* type check class definition and inheritance
* type check constructor calls
* type check method calls for arguments and return value
* type check method overrides
* make instances of TClass be treated like any other type

## misc
* switch Docker image from debian to ubuntu
* add tests for membervariables, methods and inheritance
