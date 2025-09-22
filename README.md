# SPaRo: Split Pair and Random Rotate

## Overview

Given a set of n (even) distinct members, this algorithm randomly matches two members to create n/2 pairs with the following constraints:
- a member can't be matched with itself -> self loops not allowed
- matching is bidirectional -> A matches to B automatically means B matches to A
- a member can't be matched with more than one member -> all pairs are disjoint groups of two
- if we repeat the matching algorithm, no two members can be matched repeatedly in subsequent iterations -> pairs are unique in subsequent iteration
- if n is odd, then one and only one member is matched to a dummy member -> a dummy member is created to make number of members even
- members can be added or removed from the list -> each such operation requires to trigger the sparro algorithm

## Algorithm at sketch level

In simple terms algorithm works as follows:
1. read a list of members (from .json or so)
2. add a dummy entry if the length of the list is odd
3. randomly shuffle the list
4. split the list into two equal part and call them group A and group B
5. initial match is all paris at same index in both group: (A_i, B_i)
6. for all subsequent runs of the algorithm, rotate the list B by one place -> we call it vertical rotation in B
7. then randomly select one (or more but less than N/2) indices from list A and swap the members in those indices in list A and B -> we call it horizontal random rotation
8. then the match is again (A_i, B_i) with this new configuration
9. maintain states of list A and list B and repeat steps 6, 7, 8

Note: the random horizontal rotation does not alter the pairs in one iteration as pairs are bidirectional, but randomizes (or pseudo-randomize) the pair formation in the subsequent iteration when combined with vertical rotation on list B.

## Quick start

To use this algorithm on your data, please follow the steps:
1. Clone this repo: ```git clone https://github.com/tatban/Sparro.git```
2. Create a .json file as shown in ```data.json``` file and add your members' information. 'email' field is used as id, so it has to be unique
3. run the following command:
```commandline
python main.py -d <path/to/input.json> -n <group name> -o <path/to/output.json>
```
4. for all subsequent runs, use the previous run's output json as input to maintain the matching state consistency to comply with the constraints mentioned in Overview

### A concrete example:
with the provided ```data.json``` file we can do:
```commandline
python main.py -d "data.json" -n "Test Group" -o "matched_result.json"
```

## Future Scope

This algorithm can be used to many different context with different peripheral code on top of it. Here are few ideas, feel free to work on and give PR:
1. Add some structured data loading pipeline with one base loader inherited by multiple loaders for loading from json, csv, text, google sheets etc. 
2. Wrap it with a FastAPI, make endpoints on adding and removing members and automate the triggering of this algorithm in a fixed interval and when the state gets dirty i.e. some member is added or removed
3. Write an automatic emailing system -> for each run of the matching algorithm matched pairs get notified in email about their new matched "partner"

## Acknowledgement
This code is developed as a side project by me ([Tathagata Bandyopadhyay](https://tatban.github.io/)), while doing a research internship at the ["Autonomous Learning Group"](https://uni-tuebingen.de/fakultaeten/mathematisch-naturwissenschaftliche-fakultaet/fachbereiche/informatik/lehrstuehle/distributed-intelligence/home/) headed by [Prof. Dr. Gerog Martius](https://uni-tuebingen.de/fakultaeten/mathematisch-naturwissenschaftliche-fakultaet/fachbereiche/informatik/lehrstuehle/distributed-intelligence/team/prof-dr-georg-martius/) at the [University of Tübingen](https://uni-tuebingen.de/). The project was inspired by an immediate application in automating the solution of "research buddy pairing" problem within this amazing group. I thank everyone in this group for all the fruitful discussions motivation and support to work on this project.
