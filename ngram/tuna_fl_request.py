import logging
import sys
from os import listdir
from os.path import join, isfile, isdir
from pathlib import Path

from cmd_utils import shellCallTemplate
from file_search import contains
from git_utils import clone_checkout

TUNA_FL_JAR = join(Path(__file__).parent, 'fl-1.0-jar-with-dependencies.jar')
TUNA_FL_OUTPUT_CSV_FILE_NAME = 'tuna_fl.csv'
# todo refactor based on _output_filename_prefix_by_tokenizer(tokenizer)
JP_TUNA_FL_OUTPUT_CSV_FILE_NAME = TUNA_FL_OUTPUT_CSV_FILE_NAME
UTF8_TUNA_FL_OUTPUT_CSV_FILE_NAME = 'UTF8' + TUNA_FL_OUTPUT_CSV_FILE_NAME

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler(sys.stdout))


class FileRequest:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def _abs_path(self, repo_path) -> str:
        abs_file_path = join(repo_path, self.file_path)
        if not isfile(abs_file_path):
            log.error('ignored not existing file {0}'.format(abs_file_path))
            return None
        else:
            return abs_file_path

    def to_str(self, repo_path: str) -> str:
        abs_file_path = self._abs_path(repo_path)
        if abs_file_path is None:
            return None
        return "'-in=" + abs_file_path + "'"


class TunaFlRequest:

    def __init__(self, file_requests, repo_path: str, output_dir: str,
                 output_filename=TUNA_FL_OUTPUT_CSV_FILE_NAME, progress_file='p_log.out',
                 force_reload=False, tokenizer=None):
        self.repo_path: str = str(Path(repo_path).absolute())
        self.file_requests = file_requests
        self.output_dir = output_dir
        self.output_filename = output_filename
        self.locs_output_file = join(output_dir, output_filename)
        self.force_reload = force_reload
        self.progress_file = progress_file
        self.tokenizer = tokenizer

    def has_output(self) -> bool:
        return self.has_locs_output()

    def has_locs_output(self) -> bool:
        return isfile(self.locs_output_file)

    def to_str(self) -> str:
        fr = set(filter(None, {s.to_str(self.repo_path) for s in self.file_requests}))
        if len(fr) > 0:
            res = " ".join(fr) + " -out=" + self.locs_output_file + " -repo=" + self.repo_path + " -ex_w_in_path=test"
            if self.tokenizer is not None:
                res = res + " -tokenizer=" + self.tokenizer
            return res
        else:
            log.error('MbertLocationsRequest failed to collect any input files {0}'.format(self.repo_path))
            return None

    def preprocess(self) -> bool:
        return True

    def _call_tuna_fl(self, jdk_path: str, tuna_fl_jar: str):
        request = self.to_str()
        if request is None:
            log.error('Empty request {0}'.format(self.repo_path))
            return False
        cmd = "JAVA_HOME='" + jdk_path + "' " + join(jdk_path, 'bin',
                                                     'java') + " -jar " + tuna_fl_jar + " " + request
        print("call mbert cmd ... {0}".format(cmd))
        output = shellCallTemplate(cmd)
        log.info(output)
        return isfile(self.locs_output_file)

    def has_executed(self) -> bool:
        line_done = self.locs_output_file + ',' + 'exit'
        return self.progress_file is not None and contains(self.progress_file, line_done)

    def _print_progress(self, status, reason, locs_output_file):
        def progress_line(file, stat, reas):
            return file + ',' + stat + ',' + reas

        if self.progress_file is not None:
            with open(self.progress_file, mode='a') as p_file:
                if isinstance(locs_output_file, list):
                    line = "\n".join([progress_line(f, status, reason) for f in locs_output_file])
                else:
                    line = progress_line(locs_output_file, status, reason)
                print(line, file=p_file)

    def call(self, jdk_path: str, tuna_fl_jar: str = TUNA_FL_JAR) -> str:
        if not self.force_reload and self.has_output():
            self.on_exit('exit_has_output')
            return None
        if not self.preprocess():
            self.on_exit('exit_preprocess')
            return None
        if not self.has_locs_output():
            if not self._call_tuna_fl(jdk_path, tuna_fl_jar):
                self.on_exit('exit_call_tuna')
                return None
        self.on_exit('done')
        return self.locs_output_file

    def on_exit(self, reason):
        self._print_progress('exit', reason, self.locs_output_file)

    @staticmethod
    def call_static(req, jdk_path: str, tuna_fl_jar: str = TUNA_FL_JAR):
        req.call(jdk_path, tuna_fl_jar)
        return req


class RemoteTunaFlRequest(TunaFlRequest):
    def __init__(self, vcs_url: str, rev_id: str, *args, **kargs):
        super(RemoteTunaFlRequest, self).__init__(*args, **kargs)
        self.vcs_url = vcs_url
        self.rev_id = rev_id

    def preprocess(self) -> bool:
        # checkout project.
        from git import GitCommandError
        try:
            if not isdir(self.repo_path) or len(listdir(self.repo_path)) == 0:
                clone_checkout(self.vcs_url, self.repo_path, self.rev_id)
            return isdir(self.repo_path) and len(listdir(self.repo_path)) > 0
        except GitCommandError:
            log.error('failed to clone and checkout repo {0} {1}'.format(self.vcs_url, self.rev_id))
            import traceback
            traceback.print_exc()
            return False

    def on_exit(self, reason):
        super(RemoteTunaFlRequest, self).on_exit(reason)
        if isdir(self.repo_path):
            import shutil
            shutil.rmtree(self.repo_path)


def _output_filename_prefix_by_tokenizer(tokenizer):
    return '' if tokenizer is None or tokenizer == '' or tokenizer == 'JP' else tokenizer


class MultiTokenizerRequest(RemoteTunaFlRequest):
    def __init__(self, tokenizers: list, *args, **kargs):
        super(MultiTokenizerRequest, self).__init__(*args, **kargs)
        self.locs_output_files = {
            t: join(self.output_dir, _output_filename_prefix_by_tokenizer(t) + self.output_filename) for t in
            tokenizers}
        self.locs_output_file = None
        self.tokenizer = None

    def call(self, jdk_path: str, tuna_fl_jar: str = TUNA_FL_JAR) -> str:
        for tokenizer in self.locs_output_files:
            self.locs_output_file = self.locs_output_files[tokenizer]
            self.tokenizer = tokenizer
            super(MultiTokenizerRequest, self).call(jdk_path, tuna_fl_jar)
        if isdir(self.repo_path):
            import shutil
            shutil.rmtree(self.repo_path)
        return None

    def on_exit(self, reason):
        super(RemoteTunaFlRequest, self).on_exit(reason)

    def has_executed(self) -> bool:
        lines_done = [lof + ',' + 'exit' for lof in self.locs_output_files.values()]
        return self.progress_file is not None and contains(self.progress_file, lines_done)
