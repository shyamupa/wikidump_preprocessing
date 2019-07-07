import gzip
import logging

def parse_schema(filename, encoding):
    """
    Parameters
    ----------------
    filename: str
        The filename for the data file

    Returns
    ---------------
    Dictionary that maps field name to zero indexed number
    For instance, given:
    ...
    `page_id` int(8) unsigned NOT NULL AUTO_INCREMENT,
    `page_namespace` int(11) NOT NULL DEFAULT '0',
    `page_title` varbinary(255) NOT NULL DEFAULT '',
    `page_restrictions` tinyblob NOT NULL,
    ...
    This should return {`page_id` : 0, `page_namespace` : 1, `page_title` : 2, `page_restrictions` : 3}
    """
    schema = {}
    logging.info("Parsing schema for %s", filename)
    f = gzip.open(filename, "rt", encoding=encoding)
    start_parse = False
    fields = []
    for line in f:
        if start_parse:
            if "PRIMARY KEY" not in line:
                fields.append(line)
            else:
                break
        else:
            if not line.startswith("CREATE TABLE"):
                continue
            else:
                start_parse = True
    f.close()
    for i, s in enumerate(fields):
        schema[s.split()[0][1:-1]] = i
    return schema

def split_str(split_char, split_str):
    """
    Parameters
    -------------
    split_char: char
        The character to split upon
    split_str: str
        The string to split

    Returns
    -------------
    List of string tokens splitted by split_char
    
    This takes care of corner cases such as quotation: "xx,xx" and escape character, 
    which will not be handled correctly by python split function.
    """
    return_list = []
    i = 0
    last_pos = 0
    while i < len(split_str):
        if split_str[i] == '\'':
            i += 1
            while split_str[i] != '\'' and i < len(split_str):
                if split_str[i] == '\\':
                    i += 2
                else:
                    i += 1
        else:
            if split_str[i] == split_char:
                return_list.append(split_str[last_pos:i])
                last_pos = i + 1
        i += 1
    return_list.append(split_str[last_pos:])
    return return_list
