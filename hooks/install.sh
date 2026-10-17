#!/bin/sh
cp hooks/pre-push .git/hooks/pre-push && chmod +x .git/hooks/pre-push && echo "installed .git/hooks/pre-push"
