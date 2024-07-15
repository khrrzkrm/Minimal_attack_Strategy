# Minimal attack strategy:

This project's goal is to reason about vulnerabilities of an information system specified as a Timed attack tree with Costs. 
Written in Python and using the Z3 solver, the tool computes the feasibility of an attack as well as synthesizes a minimal-cost model from all possible attacks.

![Algebraic Tree Definitions](https://latex.codecogs.com/png.latex?\text{AT}%20::=%20&%20(\text{Node},%20\text{AT},%20\text{AT})%20\mid%20\text{Leaf}%20\\%20\text{Node}%20::=%20&%20(idt,\text{gate},%20\mathbb{I})%20\\%20\text{Leaf}%20::=%20&%20(idt,%20\text{cost},%20\delta)\\%20\text{gate}%20\in%20&%20~\{\text{AND,%20OR}\})


## Installation
Python 3.11.3 or above.

Z3 library in python:
```
pip install z3-solver
```
Latex:
```
sudo apt-get install texlive-full
```
## Example Usage

```
py paper_example.py
```
 or
```
py extended_example.py
```


## Features
- draw_attack_tree: Draw attack trees as PDF from a specified.
- Propagate: Propagates the interval from the upper nodes down to the lower nodes, fails when a sufficient conflicting condition holds.
- synthesize: Computes a model of an attack defeating the attack, else returns the leaves that are time conflicting with each other.
- optimize: Computes the minimal cost attack defeating the attack tree.


