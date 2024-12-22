import json
from os import PathLike
from typing import Literal, Self
from collections.abc import Generator
from pathlib import Path

StrOrBytesPath = str | bytes | PathLike[str] | PathLike[bytes]
LiteralFile = Literal["normals.json", "ar.json", "diep.json"]

ROOT = "basic"
NO_PARENT = "None"

class TankTree:
    """
    TankTree class representing a tree of a lot the tanks from games
    likes arras.io or diep.io

    init: 
        tree: the tank tree

    alternate initializer (classmethod):
    
    load_tree: 
        filename: file to be read and json parsed to be used as the tre
                  accepts StrOrBytesPath and has Literals for the inbuilt
                  arras and diep trees

    `properties`

    tree: the tree passed in the initalizer
    supports setting

    tanks: a list of all the unique tanks
    caching property, once accessed, will
    use its cache if the tree wasnt changed

    table: a dictionary where the key is the tank name 
    (all keys are unique, meaning table.keys() gives you
    the tanks attribute) and the value is an integer of
    how many times the tank appears in the tree

    `methods`

    get_strict(int) -> list[str]
    returns a list of tanks which appear `n`
    amount of times in the tree


    """

    def __init__(self, tree: dict[str, dict | list]) -> None:
        self._tree = tree
        self._cached_table = None
        self._cached_tanks = None

    @classmethod
    def load_tree(cls, filename: StrOrBytesPath | LiteralFile) -> Self:
        with open(filename) as f:
            return cls(json.load(f))
            
    @property
    def tree(self) -> dict[str, dict | list]:
        return self._tree

    @tree.setter
    def tree(self, value: dict):
        self._tree = value
        self._cached_table = None
        self._cached_tanks = None
        
    @property
    def tanks(self) -> list[str]:
        return list(self.table.keys())
    
    @property
    def table(self) -> dict[str, int]:
        """
        returns dict[str, int]

        returns a dictionary containing the tanks' name and the amount of times
        they are found in the class tree
        """

        # Despite using globals seems like a bad idea
        # here using globals instead of a return
        # makes it simpler

        if self._cached_table is not None:
            return self._cached_table

        table = dict()

        def get_appearances(item: dict = self.tree):
            """internal method"""

            for k, v in item.items():
                get = table.get(k, None)
                if get is None:
                    table[k] = 1
                else:
                    table[k] += 1


                if isinstance(v, dict):
                    get_appearances(v)

                elif isinstance(v, list):
                    for tank in v:
                        get = table.get(tank, None)
                        if get is None:
                            table[tank] = 1
                        else:
                            table[tank] += 1
        
        get_appearances()
        self._cached_table = table
        return table

    def get_strict(self, n: int) -> list[str]:
        """return a list of strings of tank names, where they appear `n` of times in the class tree"""

        return [name for name, amt in self.table.items() if amt == n]

    def get_highest(self) -> dict[str, int]:
        """
        returns a dictionary of the most amount of times a tank has been seen in the class tree
        if theres multiple with the same amount, we return all with the highest group amount
        """
        highests: set[int] = set()
        returner: dict[str, int] = dict()
        highests.add(-1)

        for tank, amount in self.table.items():
            maximum = max(highests)
            highests.add(amount)

            if amount > maximum:
                returner = {tank: amount}

            elif amount == maximum:
                returner[tank] = amount

        return returner

    def get_lowest(self) -> dict[str, int]:
        """
        returns a dictionary of the least amount of times a tank has been seen in the class tree
        if theres multiple with the same amount, we return all with the lowest group amount
        """
        lowests: set[int] = set()
        returner: dict[str, int] = dict()
        lowests.add(9999999)

        for tank, amount in self.table.items():

            minimum = min(lowests)
            lowests.add(amount)

            if amount < minimum:
                returner = {tank: amount}

            elif amount == minimum:               
                returner[tank] = amount

        return returner

    def get_raw_tree(self, grapth = dict()) -> Generator[str]:
        """
        # Generator internal method
        """
        if not grapth:
            grapth = self.tree

        for k, v in grapth.items():
            yield k
            if isinstance(v, list):
                for i in v:
                    yield i
            elif isinstance(v, dict):
                yield from self.get_raw_tree(v)

    def startswith(self, name: str) -> list[str]:
        """returns a list of tank names that start with `name`"""
        return [tank for tank in self.table.keys() if tank.startswith(name)]

    def is_in(self, text: str) -> list[str]:
        """returns a list of tank names that have `text` in their name"""
        return [tank for tank in self.table.keys() if text in tank]

    def get_paths(
            self, tank: str, /, *, _grapth: dict | None = None, _path: tuple = ()
            ) -> Generator[list[str], None, None]:
        """
        # Generator Method

        returns a list which contains lists for every path to the tank

        ("triplex") ->  [["basic", "twin", "helix", "triplex"], ["basic", "desmos", "helix", "triplex"]]

        """
        grapth = _grapth
        path = _path

        if grapth is None:
            grapth = self.tree
        

        for key, leaf in grapth.items():
            # print(f"New call: {key=}\n{leaf=}")
            if key == tank:
                # print(f"key is tank, path: {[*path, tank]}, {key=}")
                yield [*path, tank]

            elif isinstance(leaf, list):
                if tank in leaf:
                    # print(f"Found tank in {leaf}, path: {[*path, tank]}")
                    yield [*path, key, tank]

            elif isinstance(leaf, dict):
                # print(f"Creating a new recursion call...\n{tank, leaf, path + (key,)}")
                yield from self.get_paths(tank, _grapth=leaf, _path=(path + (key,)))

def make_file(arras: TankTree, top: Path, filename: str) -> Path:
    r"""
    create `filename.md` in `top`

    C:\Users\User\top\filename.md

    return path pointing to this file
    """

    name = (top / filename).with_suffix(".md")

    # XXX this is hardcoded, be careful
    if filename == ROOT:
        parent = NO_PARENT
    elif (parent := top.name) == filename:
        parent = top.parent.name

    all_paths = ["all paths:\n"]
    current_path = None

    for path in arras.get_paths(filename):
        all_paths.append(f"  {"/".join(path)}\n")
        if len(path) >= 2 and not current_path:
            if path[-2] == parent:
                current_path = "/".join(path)


    with name.open("w") as file:
        file.write("\n".join(
            [
             f"name: {filename}", 
             f"parent: {parent}",
             f"current path: not implemented",
             *all_paths
            ]
        ))

    return name

def create(arras: TankTree, TOP: dict[str, dict | list], PATH: Path):
    """
    arras: the tree, this is used to get_paths from it
    TOP: is the tank tree in raw form
    PATH: is where is going to be the top path
    """
    for tank, item in TOP.items():
        if not item:
            make_file(arras, PATH, tank)
            return
        else:
            (path := (PATH / tank)).mkdir(exist_ok=True)
            make_file(arras, path, tank)

            if isinstance(item, list):  
                for t in item:      
                    make_file(arras, path, t) 

            elif isinstance(item, dict):
                create(arras, item, path)

            else:
                raise ValueError(f"what the fuck? {type(item)=}")



def path_searcher(tree: TankTree):
    """CLI tank path searcher"""

    to_print = \
    """type out a tank's name to view all paths to the tank
    .all: show all tanks
    .count: how many unique tanks are there
    .highest: tank that is seen the most in the tree
    .lowest: tanks that are seen the least in the tree
    """

    print(to_print)

    while True:

        tank = input(">>> ")

        if tank.startswith("."):

            tank = tank.removeprefix(".")

            match tank:

                case "all":
                    for tank in tree.tanks:
                        print(tank)                    

                case "count":
                    print(len(list(set(tree.tanks))))

                case "highest":
                    for tank, count in tree.get_highest().items():
                        print(f"{tank}: {count}")

                case "lowest":
                    for tank, count in tree.get_lowest().items():
                        print(f"{tank}: {count}")

            continue

        elif not tank.strip():
            continue

        paths = list(tree.get_paths(tank))

        if not paths:

            lowered = tank.lower()

            if lowered in tree.tanks:
                print(f"No tank found for '{tank}', did you mean '{lowered}'?")
                continue

            elif (dash := "-".join(lowered.split(" "))) in tree.tanks:
                print(f"No tank found for '{tank}', did you mean '{dash}'?")
                continue

            elif lowered == "triangle":
                print("No, it's with a dash, did you mean tri-angle?")
                continue

            print(f"No tank found for '{tank}'")
            continue

        for item in paths:
            print("/".join(item))

diep = TankTree.load_tree("diep.json")
#arras = TankTree.load_tree("normals.json")
#arras_ar = TankTree.load_tree("ar.json")

PATH = Path(r"..\tanks")

create(diep, diep.tree, PATH)