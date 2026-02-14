import os

FILE_PATH = "external_code.py"

def indent_content(content):
    if not content: return ""
    # Reemplaza dobles comillas por simples y añade 4 espacios
    content = content.replace('"', "'")
    lines = content.split("\n")
    return "\n".join(["    " + l if l.strip() else "" for l in lines])

def get_rules():
    try:
        with open(FILE_PATH, "r") as f:
            content = f.read()
    except OSError:
        return "", []

    tag = "#RULE:"
    if tag not in content:
        return content, []

    # Separamos la cabecera (lo que está antes del primer #RULE:)
    parts = content.split(tag)
    header = parts[0]
    
    # El resto son las reglas, restaurando el tag eliminado por split
    rules = [tag + p for p in parts[1:]]
    return header, rules

def save_rules(header, rules_list):
    with open(FILE_PATH, "w") as f:
        # Unimos cabecera y reglas
        f.write(header + "".join(rules_list).strip() + "\n")

def manage_rules(command, name=None, content=None):
    header, rules = get_rules()

    if command == "/rule_list":
        names = []
        for r in rules:
            linea = r.split("\n")[0]
            names.append(linea.replace("#RULE:", "").strip())
        return ", ".join(names) if names else "No hay reglas."

    if command == "/rule_show":
        for r in rules:
            if ("#RULE:" + name) in r:
                return r.strip()
        return "Error: No existe."

    if command == "/rule_del":
        new_rules = [r for r in rules if ("#RULE:" + name) not in r]
        if len(new_rules) == len(rules): return "Error: No existe."
        save_rules(header, new_rules)
        return "Rule eliminada."

    if command == "/rule_add":
        for r in rules:
            if ("#RULE:" + name) in r: return "Error: Ya existe."
        indented = indent_content(content)
        new_rule = "\n\n    #RULE:" + name + "\n" + indented
        rules.append(new_rule)
        save_rules(header, rules)
        return "Rule añadida."

    if command == "/rule_change":
        found = False
        indented = indent_content(content)
        for i, r in enumerate(rules):
            if ("#RULE:" + name) in r:
                rules[i] = "\n    #RULE:" + name + "\n" + indented + "\n"
                found = True
                break
        if not found: return "Error: No existe."
        save_rules(header, rules)
        return "Rule modificada."

    return "Comando no reconocido."

def procesar_comando(mensaje_recibido):
    # Split posicional para MicroPython
    partes = mensaje_recibido.split(None, 2)
    if not partes: return ""
    
    comando = partes[0].lower()
    if len(partes) < 2 and comando != "/rule_list":
        return "Usa: /comando NOMBRE [contenido]"

    nombre = partes[1] if len(partes) > 1 else ""
    contenido = partes[2] if len(partes) > 2 else ""

    # Ejecutar gestión y retornar resultado
    return manage_rules(comando, nombre, contenido)

def multi_replace(txt):
    return txt.replace('"', "'")