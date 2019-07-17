
from rre.redos import find_match, find_redos

def test():
    print(find_redos(r"(!+)+h"))
    print(find_redos(r"(m(a|bc)*|mbca)*h"))
    print(find_redos(r"^(([a-z])+.)+[A-Z]([a-z])+$"))
    print(find_redos(r"([a-zA-Z]+)*h"))
    print(find_redos(r"(a+)+h"))
    print(find_redos(r"(a|aa)+h"))
    print(find_redos(r"(a|a?)+h"))
    print(find_redos(r"^([a-zA-Z0-9])(([\-.]|[_]+)?([a-zA-Z0-9]+))*(@){1}[a-z0-9]+[.]{1}(([a-z]{2,3})|([a-z]{2,3}[.]{1}[a-z]{2,3}))$"))
    print(find_match(r"^([a-zA-Z0-9])(([\-.]|[_]+)?([a-zA-Z0-9]+))*(@){1}[a-z0-9]+[.]{1}(([a-z]{2,3})|([a-z]{2,3}[.]{1}[a-z]{2,3}))$"))


if __name__ == "__main__":
    test()
