# code from https://github.com/jupyter-resources/notebook-research/blob/2a81d2853ceeb57b8d9db22ca6cb12f01d84bd50/scripts/extract_data.py#L669
# slight modifications
import numpy as np
import pandas as pd
import ast

def parse_py_ast(list_of_code):
    """ Parse imports, functions, and classes for Python code cells. """

    imports = []
    functions = []
    classes = []
    parsed_ast = False

    # Remove magic lines because AST doesnt understand magic.
    if None not in list_of_code:
        code = "\n".join([c for c in list_of_code if
            not c.startswith("%") and
            not c.startswith("!") and
            not c.startswith("?")
        ]).replace(";"," ")
    else:
        code = ""

    def search_tree(tree):
        for t in tree.body:
            if type(t) == ast.ClassDef:
                class_name = t.name
                methods = []
                attributes = []
                for b in t.body:
                    if type(b) == ast.FunctionDef:
                        methods.append(b.name)
                    elif type(b) == ast.Assign:
                        try:
                            attributes.append(b.targets[0].id)
                        except Exception:
                            attributes.append("")
                classes.append([class_name, len(methods), len(attributes)])

            elif type(t) in [ast.ImportFrom, ast.Import]:
                for name in t.names:
                    n = name.name
                    asname = name.asname
                    if asname == None:
                        asname = n

                    if type(t) == ast.ImportFrom:
                        module = t.module
                        if module != None and n != None:
                            n = module+"."+n

                    imports.append([n, asname])

            elif type(t) == ast.FunctionDef:
                name = t.name
                args = [arg.arg for arg in ast.walk(t.args) if type(arg) == ast.arg]
                functions.append([name, args])

            elif type(t) == ast.Assign and type(t.value) == ast.Lambda:
                try:
                    name = t.targets[0].id
                except Exception:
                    name = ""
                args = [arg.arg for arg in ast.walk(t.value.args) if type(arg) == ast.arg]
                functions.append([name, args])

    # Try to parse the entire cell.
    try:
        tree = ast.parse(code)
        parsed_ast = True
        search_tree(tree)

    # Exception due to syntax error in code. Try line by line.
    # We could still miss a multi-line import, but better than nothing.
    except Exception:
        for c in code.split("\n"):
            try:
                tree = ast.parse(c)
                parsed_ast = True
                search_tree(tree)

            except Exception:
                continue

    return imports, functions, classes, parsed_ast

def parse_py(cell_info):
    """ Parse imports, functions, classes, and comments for Python code cells. """

    imports, functions, classes, parsed_ast = parse_py_ast(cell_info["code"])
    cell_info["imports"] = imports
    cell_info["parsed_ast"] = parsed_ast
    cell_info["functions"] = functions
    cell_info["classes"] = classes
    cell_info["num_imports"] = len(imports)
    cell_info["num_functions"] = len(functions)
    cell_info["num_classes"] = len(classes)

    # Split "code" into "comments" and "code".
    in_multiline = False
    for l in cell_info["code"]:
        if l == None:
            l = ''
        l = l.strip()
        has_sep = False
        for sep in [""""","""""]:
            if sep in l:
                has_sep = True
                if not in_multiline:
                    comment = l.split(sep)[1:]
                    cell_info["num_comments"] += 1
                    comment = comment[0].strip()
                    if comment != "":
                        cell_info["comments"].append(comment)
                    if len(l.split(sep)) == 2:
                        in_multiline = True
                else:
                    comment = l.split(sep)[0].strip()
                    if len(l.split(sep)) > 2:
                        # Starts a new comment on same line.
                        # Add both comments, still in multiline.
                        second_comment = l.split(sep)[2]
                        cell_info["num_comments"] += 1
                        if comment != "":
                            cell_info["comments"].append(comment)
                        if second_comment != "":
                            cell_info["comments"].append(second_comment)
                    else:
                        if comment != "":
                            cell_info["comments"].append(comment)
                        in_multiline = False
        if not has_sep and in_multiline:
            cell_info["comments"].append(l)

        if "#" in l:
            cell_info["num_comments"] += 1
            cell_info["comments"].append(" ".join(l.split("#")[1:]).strip())

    return cell_info

def parse_r_imports(list_of_code):
    """ Parse imports for R code cells """
    imports = []
    for code in list_of_code:
        code = code.replace("\\n","").replace("\n","")
        im = None
        if "library(" in code and not code.startswith("#"):
            im = code.split("library(")[1].split(")")[0]
            imports.append((im, ""))

        if "require(" in code and not code.startswith("#"):
            im = code.split("require(")[1].split(")")[0]
            imports.append((im,""))

    return imports

def parse_r(cell_info):
    """ Parse imports, functions, and comments for R code cells. """

    cell_info["imports"] = parse_r_imports(cell_info["code"])

    for l in cell_info["code"]:
        l = l.lstrip()

        if "function" in l:
            if "<-" in l:
                cell_info["functions"].append(l.split("<-")[0].strip())
                cell_info["num_functions"] += 1
            elif "=" in l:
                cell_info["functions"].append(l.split("=")[0].strip())
                cell_info["num_functions"] += 1

        elif "#" in l:
            cell_info["num_comments"] += 1
            cell_info["comments"].append(" ".join(l.split("#")[1:]).strip())

    return cell_info

def parse_ju_imports(list_of_code):
    """ Parse imports for Julia code cells """
    imports = []
    for code in list_of_code:
        if code.strip().startswith("using") and code.split("using")[1].strip() != "":
            im = code.split("using")[1].strip().split()[0]
            if im.endswith(":"):
                im = im[:-1]
                rest = code.split(":")[1].strip().split(",")
                for r in rest:
                    imports.append((im+"."+r.strip(), r.strip()))
            else:
                imports.append((im,""))
        elif code.strip().startswith("import") and code.split("import")[1].strip() != "":
            im = code.split("import")[1].strip().split()[0]
            imports.append((im,""))
    return imports

def parse_ju(cell_info):
    """ Parse imports, functions, and comments for Julia code cells. """

    cell_info["imports"] = parse_ju_imports(cell_info["code"])

    in_multiline = False
    for l in cell_info["code"]:
        l = l.lstrip()
        parts = l.split()
        if len(parts) >= 2:
            if l.startswith("def"):
                cell_info["functions"].append(parts[1].split("(")[0])
                cell_info["num_functions"] += 1
            elif l.startswith("class"):
                cell_info["classes"].append(parts[1].split(":")[0])
                cell_info["num_classes"] += 1

        if in_multiline:
            cell_info["num_comments"] += 1
            cell_info["comments"].append(l)

        if l.startswith("#="):
            if not in_multiline:
                cell_info["num_comments"] += 1
                cell_info["comments"].append(l.replace('"',""))
                in_multiline = True
        elif l.startswith("=#"):
            if in_multiline:
                in_multiline = False
        elif "#" in l:
            cell_info["num_comments"] += 1
            cell_info["comments"].append(" ".join(l.split("#")[1:]).strip())

    return cell_info
