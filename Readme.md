# n-gram Naturalness-based lines ranking

You can call `ngram/tuna_fl_request.py` to rank java file lines by cross-entropy (naturalness).

The script mainly calls the jar `java-n-gram-line-level-1.0.0-jar-with-dependencies.jar` built from this implementation: https://github.com/Ahmedfir/java-n-gram-line-level.git


### Typical usage: 
- input: List of java files from a project, whose lines will be ranked.
- training input: the rest of java files from that same project.
- output: ranked List of lines of the input files, by cross-entropy.

### License: 
Apache 2.0

