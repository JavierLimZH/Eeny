# Eeny

#### Standard Eeny Meeny setup: count 20 times in a circle

```
Alice 1: Alice Bob Charlie;
Bob 1;
Charlie 1;

Alice < 20;
```

In the above example, we define 3 people. Alice, Bob, and Charlie. Alice has a cycle, consisting of the three. 

On the final line, we state that Alice will be the first counter. Alice counts 20 times, hence landing on Charlie. 

Charlie now becomes the counter. He has no cycle, hence halts. The final state is of Alice pointing to Charlie, and Charlie being the final counter.

##### Notes

Had Alice landed on herself, (eg counting 19), she would then, again start counting. This time, only counting once, ending on Bob.

The `1` after Bob and Charlie's definition can be excluded, it will be implicitly assumed to be 1.

### Structures

It is common to reuse certain arrangements of counters. This can be made cleaner with structures.

```
// One Bit Memory Structure
Demux_1bit {
    // input nodes
    Write0 1: C;
    Write1 2: C;
    DemuxI 2: C;
    ResetI 5: C;

    // reset loop
    ResetResetO 5: C;
    ResetSig0 4: C;
    ResetSig1 3 : C;
    ResetDemux0 2: C;
    ResetDemux1 1: C;

    // central counter 
    C:  
        Sig0 
        Sig1 
        Demux0 
        Demux1 

        ResetResetO
        ResetSig0
        ResetSig1
        ResetDemux0
        ResetDemux1

        ResetO;

    // terminal nodes
    Sig0;
    Sig1;
    Demux0;
    Demux1;
    ResetO;
}

// use it
mem = Demux_1bit;

mem.Sig0: mem.DemuxI;
mem.Write0 <;
// ends at mem.Demux0
```

### IO

A simple extension to the current definition would be to allow basic IO, through the use of special counters. Here we introduce input (?) and output (!) counters.

#### Output counters

If a counter's definition is prefixed by a `!`, then in addition to its normal behavior, it also outputs the character corresponding to the ascii of the incoming count value. 

For instance,

```
start 72: chr0;
!chr0 105: chr1;
!chr1 33: end;
!end;

start <;
```

outputs `Hi!`

#### Input counters

If a counter's definition has a `?` instead of a count value, then it receives one character from stdin and uses its ascii value instead. It will not "remember" the character inputted, it receives one character each time.

For instance,

```
input ?: output;
!output: input;

input <;
```

Would be an echo program, simply repeating stdin to stdout.

`?` may also be used in place of the initial trigger count.

```
start < ?;
```

### Samples

#### Truth Machine

If the input is `0`, output `0` and halt. else, if the input is `1`, output `1` forever.

```c
// if 0 (48), count even number and land on zero
// if 1 (49), count odd number and land on one
split 1: one zero;

// send 48 to output counter
zero 48: output_zero;
// output, and halt
!output_zero;

// send 49 to output counter
one 49: output_one;
// output, and send another 49 to self
!output_one 49: output_one;

// input to split
split < ?;
```

### Grammar Spec

```
start: _line* trigger*

_line: counter_def | struct_def | struct_set
trigger: name "<" count? ";"

counter_def: outp_flag? name count? (":" cycle)?  ";"

struct_def: name "{" (counter_def | struct_set)* "}"
struct_set: name "=" name ";"
struct_sep: "."

!name: NAME (struct_sep NAME)*
!cycle: name+
!count: inp_flag | NUMBER

!outp_flag: "!"
!inp_flag: "?"


%import common.CNAME -> NAME
%import common.NUMBER 
%import common.WS

COMMENT: "//" /[^\n]*/ "\n"

%ignore WS
%ignore COMMENT
```



























