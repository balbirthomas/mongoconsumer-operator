# mongoconsumer

## Description

This is proof of concept demonstration charm to test MogoDB charm 
libraries. In particular this charm is a client for MonogoDB, which
implements relationship handling using libraries provided by the
MongoDB Operator.

## Build

Install the charmcraft tool

    sudo snap install charmcraft

First copy the `mongoclient.py` and `relation.py` (charm libraries) file from
the `mongodb-operator` repository into the source (`src`) directory.

Then build the charm in this git repository

    charmcraft build

## Usage

Create a Juju model for your operators, say "lma"

    juju add-model lma

Deploy a single unit of MongoDB using its default configuration

    juju deploy ./mongoconsumer.charm --resource busybox-image='busybox:latest'

## Developing

Use your existing Python 3 development environment or create and
activate a Python 3 virtualenv

    virtualenv -p python3 venv
    source venv/bin/activate

Install the development requirements

    pip install -r requirements-dev.txt

## Testing

The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. Just `run_tests`:

    ./run_tests
