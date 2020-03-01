### Usage

Two functions are provided:

```
from rre.redos import find_match, find_redos
```

`find_match` Inverses the matched text from the regular expression.

`find_redos` detects a regular expression through syntax analysis to see if there is a REDOS vulnerability; if it exists, an example of triggering the vulnerability will be given.

Unlike other simple detections, this implementation can detect deep REDOS vulnerabilities.

### Example

```
    print (find_redos (r "(! +) + h"))
    print (find_redos (r "(m (a | bc) * | mbca) * h"))
    print (find_redos (r "^ (([a-z]) +.) + [A-Z] ([a-z]) + $"))
    print (find_redos (r "([a-zA-Z] +) * h"))
    print (find_redos (r "(a +) + h"))
    print (find_redos (r "(a | aa) + h"))
    print (find_redos (r "(a | a?) + h"))
    print (find_redos (r "^ ([a-zA-Z0-9]) (([\-.] | [_] +)? ([a-zA-Z0-9] +)) * (@) { 1} [a-z0-9] + [.] {1} (([az] {2,3}) | ([az] {2,3} [.] {1} [az] {2,3 })) $ "))

    (True, '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ')
    (True, 'mbcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcambcam!')
    (True, 'a! Aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!')
    (True, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA!')
    (True, 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!')
    (True, 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!')
    (True, 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!')
    (True, '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000!')

    print (find_match (r "^ ([a-zA-Z0-9]) (([\-.] | [_] +)? ([a-zA-Z0-9] +)) * (@) { 1} [a-z0-9] + [.] {1} (([az] {2,3}) | ([az] {2,3} [.] {1} [az] {2,3 })) $ "))
    (True, '000@00.aa')
    
    
```
