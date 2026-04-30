import os
import sys
import json
from pathlib import Path

_LIB_DIR = Path(__file__).resolve().parent / "lib"

sys.path.insert(0, str(_LIB_DIR))
from vosk_cffi import ffi as _ffi

_DLL = None


def _load_dll():
    global _DLL
    if _DLL is not None:
        return _DLL
    dlldir = str(_LIB_DIR)
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(dlldir)
    os.environ["PATH"] = dlldir + os.pathsep + os.environ.get("PATH", "")
    _DLL = _ffi.dlopen(os.path.join(dlldir, "libvosk.dll"))
    return _DLL


def SetLogLevel(level):
    _load_dll().vosk_set_log_level(level)


class SpkModel:
    def __init__(self, model_path):
        self._handle = _load_dll().vosk_spk_model_new(model_path.encode("utf-8"))
        if self._handle == _ffi.NULL:
            raise Exception("Failed to create a speaker model")

    def __del__(self):
        _load_dll().vosk_spk_model_free(self._handle)


class Model:
    def __init__(self, model_path):
        self._handle = _load_dll().vosk_model_new(model_path.encode("utf-8"))
        if self._handle == _ffi.NULL:
            raise Exception("Failed to create a model")

    def __del__(self):
        _load_dll().vosk_model_free(self._handle)


class KaldiRecognizer:
    def __init__(self, *args):
        c = _load_dll()
        if len(args) == 2:
            self._handle = c.vosk_recognizer_new(args[0]._handle, args[1])
        elif len(args) == 3 and isinstance(args[2], SpkModel):
            self._handle = c.vosk_recognizer_new_spk(args[0]._handle, args[1], args[2]._handle)
        elif len(args) == 3 and isinstance(args[2], str):
            self._handle = c.vosk_recognizer_new_grm(args[0]._handle, args[1], args[2].encode("utf-8"))
        else:
            raise TypeError("Unknown arguments")
        if self._handle == _ffi.NULL:
            raise Exception("Failed to create a recognizer")

    def __del__(self):
        _load_dll().vosk_recognizer_free(self._handle)

    def SetMaxAlternatives(self, max_alternatives):
        _load_dll().vosk_recognizer_set_max_alternatives(self._handle, max_alternatives)

    def SetWords(self, enable_words):
        _load_dll().vosk_recognizer_set_words(self._handle, 1 if enable_words else 0)

    def SetPartialWords(self, enable_partial_words):
        _load_dll().vosk_recognizer_set_partial_words(self._handle, 1 if enable_partial_words else 0)

    def SetNLSML(self, enable_nlsml):
        _load_dll().vosk_recognizer_set_nlsml(self._handle, 1 if enable_nlsml else 0)

    def SetSpkModel(self, spk_model):
        _load_dll().vosk_recognizer_set_spk_model(self._handle, spk_model._handle)

    def SetGrammar(self, grammar):
        _load_dll().vosk_recognizer_set_grm(self._handle, grammar.encode("utf-8"))

    def AcceptWaveform(self, data):
        res = _load_dll().vosk_recognizer_accept_waveform(self._handle, data, len(data))
        if res < 0:
            raise Exception("Failed to process waveform")
        return res

    def Result(self):
        return _ffi.string(_load_dll().vosk_recognizer_result(self._handle)).decode("utf-8")

    def PartialResult(self):
        return _ffi.string(_load_dll().vosk_recognizer_partial_result(self._handle)).decode("utf-8")

    def FinalResult(self):
        return _ffi.string(_load_dll().vosk_recognizer_final_result(self._handle)).decode("utf-8")

    def Reset(self):
        _load_dll().vosk_recognizer_reset(self._handle)
