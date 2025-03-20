# Exercise 8

In this exercise, your task is to extend the compiler with exceptions.

As always, we already extended the parser and syntax trees, but
leave the extension of the passes to you.

The following highlights the changes we did to the code and some of
the key challenges of the exercise:

-   **Basic Idea**. We take a slightly different approach compared to the
    lecture, which is easier to integrate with the liveness analysis.

    The main challange is that when a `raise` is executed, we need to find our
    way back to the currently active exception handler, i.e the exception
    handler of the `try`-statement which is closed to the `raise` in the call
    tree.

    Instead of storing the information about exception handlers at fixed stack
    locations, as we proposed in the lecture, we are going to store it in three
    global variables, defined in `runtime.c`:

    These variables are defined in the `runtime.c` as follows:
    ```C
    int64_t* exc_sp = 0;      // Stack pointer
    int64_t* exc_fp = 0;      // Frame pointer
    int64_t* exc_handler = 0; // Address of the basic block of the
                              // currently active exception handler
    ```

    The `runtime.c` does not use those variables in any way, and it is our job
    in the compiler to define and read them.

    If we enter a `try`-block, then we save the values of those global
    variables in new temporary variables, and update their values to match the
    current function's stack and frame pointers and the address of the
    exception handler associated with the `try`-block.

    If we exit a `try`-block (without an exception) or if we enter an exception
    handler, then we restore the values of those global variables from the
    temporary variables, such that the next outer exception handler becomes
    active again.

    A `raise`-statement reads those global variables and sets the stack and
    frame pointer to those from `exc_sp` and `exc_fp`, puts the exception value
    into register `a0`, and then jumps to the address in `exc_handler`.

    This means we do not need to do any stack unwinding, because we can read
    all the information to go from a `raise` back to the currently active
    exception handler from the global variables.

-   **Liveness Troubles.** To ensure that liveness analysis still works
    correctly, we need to take special care of function calls inside of
    `try`-blocks.
    
    Without exceptions, we could simply assume, that those function calls would
    always return normally, and that eventually the instruction after a call
    would be executed.

    With exceptions, those function calls could also jump directly to the
    exception handler, and we somehow need to record this possibility in the
    control flow graph.

    Similarly, `raise`-statements that occur directly in a `try`-block require
    special treatment. The problem is that they are implemented as indirect
    jumps, i.e. jumps to an address in a register, and not as jumps to labels
    known at compile time. This means that our control flow analysis would not
    know where the indirect jump resulting from a `raise` might jump to.

    A simple solution to this problem is to add "fake" conditional jumps after
    each call- and `raise`, e.g.
    ```python
    if 0 != 0 { goto exception_handler } else { goto cont_label }
    ```
    where `exception_handler` is the label for the exception handler of the
    `try`-block, and `cont_label` is the label where the next statements of the
    `try`-block are placed.

    Even though this "fake" conditional jump, will always jump to `cont_label`,
    it will still cause the control flow graph to have an edge from after the
    call to the exception handler. This accounts for the fact that a `raise`
    inside the function call might indirectly jump to the exception handler, which
    would not be visible to our control flow graph algorithm otherwise.

    Note that jumps are only allowed at the end of basic blocks, so we need
    to start a new basic block after each call and `raies` inside of a `try`.

    Potentially, the "fake" conditional jumps could also be optimized away
    after the register allocator finished running.

    The following example illustrates what could go wrong, if we would **not**
    account for the control flow edges introduced by exceptions in function calls:
    ```python
    x = 3
    try:
      z = 666
      f()
      x = 5
    except Exception as _:
      pass
    print(x)
    ```
    Without the control flow graph edge from `f()` to the exception handler,
    the register allocator might assign `x` and `z` the same location, causing
    the `print(x)` in the end to output `666`!

    This is because without the edge it would look like `x = 5` would be
    guaranteed to come after `f()`, so `x` would not be live during `z = 666`.

-   **Top-level Exceptions.**
    To deal with exceptions that are `raise`d without being surrounded by a
    `try` (either directly or in a function further outside), we simply add
    a `try` block around the top-level statements.

    In a real compiler, one would print a nice stack-trace, but to keep it simple,
    we just print the exception value, which is always an integer.
    That way we can reuse the `print_int` function and don't need to further complicate
    the runtime and the compiler.

    We already extended the interpreter to do the same, e.g. the program
    ```python
    raise 5
    ```
    would simply print `5` on the terminal.

-   **Implementation.**
    To implement all of the above do not need any new passes.
    All the action happens in the shrinking, explicate, and instruction selection passes:

    -   In the **shrinking pass**, you need to wrap the top-level statements in a `try`-block.
        In the solution, we choose to introduce a new wrapper function around the actual
        main function, e.g. the program
        ```python
        raise 5
        ```
        would be translated to
        ```python
        def program_main():
            raise 5

        def main():
            try:
                program_main()
            except Exception as e:
                print(e)
        ```
        but you can also choose to do otherwise.

    -   In the **explicate pass**, we compile the `try`-statements
        into multiple basic blocks and lower level primitives.

        For example, the program
        ```python
        try:
           x = 5
           f()
           y = 10
        except Exception as e:
           print(e)
        print(42)
        ```
        should be compiled to
        ```python
            try_enter handler tmp_names
            x = 5
            f()
            if 0 != 0 { goto handler } else { goto try_cont }
        try_cont:
            y = 10
            try_exit tmp_names
            goto after_try
        handler:
            try_exit tmp_names
            exc_enter e
            print(e)
        after_try:
            print(42)
        ```

        The new primitives `try_enter`, `try_exit`, and `exc_enter` are translated
        away in the instruction selection pass and have the following meanings:
        
        -   `try_enter` will be compiled to code that stores the values of
            the global variables in fresh temporary variables and updates the
            global variables with the data corresponding to this `try`-statement.

            It has the exception handler label `handler` as an argument,
            because it needs to set this as the new value of the global
            variable `exc_handler`.

            Similarly, `try_exit` will be compiled to code that restores the 
            values of the global variables from the temporary variables at the
            end of a `try`-block or at the beginning of an exception handler.

            To simplify the compilation of `try_enter` and `try_exit` in the next pass,
            we already create fresh variable names `tmp_names` for the temporaries,
            and use them as arguments for both `try_enter` and `try_exit`.
            This way, we do not need to rediscover which `try_enter` belongs to
            which `try_exit` during instruction selection. `tmp_names` is an
            object of the following class:
            ```python
            @dataclass(frozen=True)
            class ExcTmpNames:
                sp: Id
                fp: Id
                handler: Id
            ```
        -   At the beginning of an exception handler, we need to run `try_exit`,
            but we also need to retrieve the `raise`d exception value from the
            register `a0` and assign it to the variable, which is used in the
            exception handler to refer to the exception (`e` in the above example).
            
            The `exc_enter e` instruction will compile down to `move e, a0`
            in the instruction selection pass.

            This is necessary, because before instruction selection, we cannot talk
            about concrete registers yet.

        Hint: You probably want to add a new parameter to the `explicate_stmts`
        and `explicate_stmt` functions, which contains the nearest exception
        handler label, or `None` if there is none in this function.

    -   In the **instruction selection** pass, you need to compile the `try_enter`,
        `try_exit`, and `exc_enter` constructs away.

        Those are rather straightforward and you basically just need to produce
        a list of instructions for each of those constructs as described above.

        To compile a `raise` away, we need an indirect jump `jr`, which
        can jump to addresses in registers instead of labels. We already added
        a corresponding `JumpIndirect` class to the subsequent syntax trees and
        passes.
  
If stuff is unclear, don't hesitate to use the chat!

Happy Coding! <3
