# Minimal attack strategy:

This project's goal is to reason about vulnerabilities of an information system specified as a Timed attack tree with Costs. 
Written in Python and using the Z3 solver, the tool computes the feasibility of an attack as well as synthesizes minimal cost models of attacks.

## Installation
Python 3.11.3 or above.
Z3 library in python:
```
pip install z3-solver

Latex:
```
sudo apt-get install texlive-full

## Usage

py .\extended_example.py or
py .\paper_example.py

## Features
- Specifying timed attack trees in attack_struct
- draw_attack_tree: Draw attack trees as PDF from a specified.
- Propagate: Propagates the interval from the upper nodes down to the lower nodes, fails when sufficient conflicting definition holds.
- synthesize: Computes a model of an attack defeating the attack, else returns the subtree that is undefeatable.
- optimize: Computes the minimal cost attack defeating the attack tree.


