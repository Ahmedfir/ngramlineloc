# n-gram Naturalness-based lines ranking

You can call `ngram/tuna_fl_request.py` to rank java file lines by cross-entropy (naturalness).

The script mainly calls the jar `java-n-gram-line-level-1.0.0-jar-with-dependencies.jar` built from this implementation: https://github.com/Ahmedfir/java-n-gram-line-level.git, 
which implementation uses Tuna APIs: https://github.com/electricalwind/tuna.git
 

##Typical usage: 
- input: List of java files from a project, whose lines will be ranked.
- training input: the rest of java files from that same project.
- output: ranked List of lines of the input files, by cross-entropy.

## Example usage:
This library has been implemented to conduct the study of naturalness captured by CodeBERT:

    @article{khanfir2022codebertnt,
        title={CodeBERT-nt: code naturalness via CodeBERT},
        author={Khanfir, Ahmed and Jimenez, Matthieu and Papadakis, Mike and Traon, Yves Le},
        journal={arXiv preprint arXiv:2208.06042},
        year={2022}
    }
- main repo: https://github.com/Ahmedfir/CodeBERT-nt
- Research paper: "CodeBERT-nt: code naturalness via CodeBERT", 
  available at: https://doi.org/10.48550/arXiv.2208.06042

  
