"""Intentionally insecure code used ONLY to show what the SAST scanner (Bandit) reports.
It is excluded from the security gate and never imported by the app."""
import hashlib
import subprocess

import yaml

PASSWORD = "admin123"  # hard-coded credential


def run(cmd):
    return subprocess.call(cmd, shell=True)  # shell injection risk


def weak_hash(data):
    return hashlib.md5(data).hexdigest()  # weak hash


def load(text):
    return yaml.load(text)  # unsafe YAML loading
