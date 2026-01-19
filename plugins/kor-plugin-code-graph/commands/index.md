---
name: index
description: Re-index the codebase to update the code graph
args: [path]
tags: [code, indexing, maintenance]
---

## Usage

Re-index a directory to update the code graph database.

## Arguments

- `path`: Directory path to index (default: current workspace)

## Notes

This command triggers a full re-index of the specified directory,
updating the symbol database with any new or changed code.
