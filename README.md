
### 使用

提供两个函数：

```
from rre.redos import find_match, find_redos
```

`find_match` 从正则表达式逆推出匹配的文本。

`find_redos` 通过语法分析来检测一个正则表达式，是否存在REDOS漏洞；如果存在，将给出一个触发漏洞的例子。

不同于其他简单的检测，这个实现可以检测出很深层的REDOS漏洞。


### Usage

Two functions are provided:

```
from rre.redos import find_match, find_redos
```

`find_match` find the matched text from the regular expression.

`find_redos` detects a regular expression through syntax analysis to see if there is a REDOS vulnerability; if it exists, an example of triggering the vulnerability will be given.

Unlike other simple detections, this implementation can detect deep REDOS vulnerabilities.


### Examples

```
    print(find_redos(r"(!+)+h"))
    print(find_redos(r"(m(a|bc)*|mbca)*h"))
    print(find_redos(r"^(([a-z])+.)+[A-Z]([a-z])+$"))
    print(find_redos(r"([a-zA-Z]+)*h"))
    print(find_redos(r"(a+)+h"))
    print(find_redos(r"(a|aa)+h"))
    print(find_redos(r"(a|a?)+h"))
    print(find_redos(r"^([a-zA-Z0-9])(([\-.]|[_]+)?([a-zA-Z0-9]+))*(@){1}[a-z0-9]+[.]{1}(([a-z]{2,3})|([a-z]{2,3}[.]{1}[a-z]{2,3}))$"))

    (True, '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    (True, 'mbcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambca!')
    (True, 'a!aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!')
    (True, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA!')
    (True, 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!')
    (True, 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!')
    (True, 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!')
    (True, '000000000000000000000000000000000000000000000000000000000000000000000000000000000!')

    print(find_match(r"^([a-zA-Z0-9])(([\-.]|[_]+)?([a-zA-Z0-9]+))*(@){1}[a-z0-9]+[.]{1}(([a-z]{2,3})|([a-z]{2,3}[.]{1}[a-z]{2,3}))$"))
    (True, '000@00.aa')
    
    
```
