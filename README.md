<div align="center">
    <img src="https://github.com/CHIMEFRB/datatrail-cli/blob/main/docs/images/Datatrail-logo.png" width="110", height="100">
</div>

<h1 align="center">Datatrail CLI</h1>

<h4 align="center">
  <a href="https://github.com/CHIMEFRB/datatrail-cli/tree/main#%EF%B8%8F-installation">Install</a>
  ·
  <a href="https://chimefrb.github.io/datatrail-cli/">Docs</a>
</h4>

<p align="center">
    <a href="https://github.com/CHIMEFRB/datatrail-cli/pulse">
      <img src="https://img.shields.io/github/last-commit/CHIMEFRB/datatrail-cli?style=for-the-badge&logo=github&color=7dc4e4&logoColor=D9E0EE&labelColor=302D41"/>
    </a>
    <a href="https://github.com/CHIMEFRB/datatrail-cli/releases/latest">
      <img src="https://img.shields.io/github/v/release/CHIMEFRB/datatrail-cli?style=for-the-badge&logo=gitbook&color=8bd5ca&logoColor=D9E0EE&labelColor=302D41"/>
    </a>
    <a href="https://github.com/CHIMEFRB/datatrail-cli/stargazers">
      <img src="https://img.shields.io/github/stars/CHIMEFRB/datatrail-cli?style=for-the-badge&logo=apachespark&color=eed49f&logoColor=D9E0EE&labelColor=302D41"/>
    </a>
    <br>
    <img alt="Coveralls" src="https://img.shields.io/coverallsCoverage/github/CHIMEFRB/datatrail-cli?logoColor=D9E0EE&style=for-the-badge&logoColor=D9E0EE&labelColor=302D41&logo=coveralls">
    <img alt="GitHub CD Workflow Status (with branch)" src="https://img.shields.io/github/actions/workflow/status/CHIMEFRB/datatrail-cli/continuous-deployment.yml?branch=main&label=Deployment&style=for-the-badge&logo=githubactions&logoColor=D9E0EE&labelColor=302D41">
    <img alt="GitHub CI Workflow Status (with branch)" src="https://img.shields.io/github/actions/workflow/status/CHIMEFRB/datatrail-cli/continuous-integration.yml?branch=main&label=Integration&style=for-the-badge&logo=githubactions&logoColor=D9E0EE&labelColor=302D41">
    <img alt="GitHub Workflow Status (with branch)" src="https://img.shields.io/github/actions/workflow/status/CHIMEFRB/datatrail-cli/docs.yml?branch=main&label=Docs&style=for-the-badge&logo=readthedocs&logoColor=D9E0EE&labelColor=302D41">
    <br>
    <img alt="GitHub issues" src="https://img.shields.io/github/issues/CHIMEFRB/datatrail-cli?style=for-the-badge&logoColor=D9E0EE&labelColor=302D41">
    <img alt="GitHub pull requests" src="https://img.shields.io/github/issues-pr-raw/CHIMEFRB/datatrail-cli?style=for-the-badge&logoColor=D9E0EE&labelColor=302D41">
    <img alt="GitHub" src="https://img.shields.io/github/license/CHIMEFRB/datatrail-cli?style=for-the-badge">
</p>

## 🛠️ Installation

### Install from PYPI

```shell
pip install datatrail-cli
```

### Clone the repository

```shell
git clone https://github.com/CHIMEFRB/datatrail-cli
cd datatrail-cli
pip install .
```

## ⚙️  Configuration

### Local

```shell
# Create Datatrail config file
datatrail config init --site local

# Ensure valid CADC Certificate exists
cadc-get-cert -u [username]
```

### CANFAR

The Configuration steps at CANFAR are similar to the local configuration.
One notable exception is that after installation, the `datatrail` command
may not be in the PATH. It is installed to `~/.local/bin`, in which case
you may need to add it to your PATH or prepend it to the follwing commands.

```shell
# Create Datatrail config file
datatrail config init --site canfar

# Ensure valid CADC Certificate exists
cadc-get-cert -u [username]
```

### CHIME

```shell
# Create Datatrail config file
datatrail config init --site chime

# Ensure valid CADC Certificate exists
cadc-get-cert -u [username]
```
