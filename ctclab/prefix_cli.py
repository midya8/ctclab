"""Strict bounded exact audit/verify with atomic file output."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .prefix_input import loads, SCHEMA
from .prefix import audit_prefix
from .prefix_verify import verify_prefix


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['audit','verify'])
    parser.add_argument('--input',required=True)
    parser.add_argument('--output')
    args=parser.parse_args(argv)
    temp=None
    try:
        if args.output and args.input!='-' and Path(args.input).resolve()==Path(args.output).resolve():
            raise ValueError('Input and output must differ')
        limit=65536 if args.mode=='audit'else 8*1024*1024
        if args.input=='-':raw=sys.stdin.buffer.read(limit+1)
        else:
            with open(args.input,'rb')as f:raw=f.read(limit+1)
        if len(raw)>limit:raise ValueError('Input byte limit exceeded')
        obj=loads(raw.decode('utf-8'),limit)
        if args.mode=='audit':out=audit_prefix(obj)
        else:
            verify_prefix(obj);out=dict(valid=True,schema=SCHEMA)
        text=json.dumps(out,ensure_ascii=True,separators=(',',':'))+'\n'
        if len(text.encode())>8*1024*1024:raise ValueError('Output byte limit exceeded')
        if args.output:
            target=Path(args.output)
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=target.parent,prefix='.ctc-prefix-',delete=False)as f:
                temp=f.name;f.write(text)
            os.replace(temp,target);temp=None
        else:sys.stdout.write(text)
        return 0
    except (ValueError,TypeError,KeyError,OSError,UnicodeError,RecursionError,OverflowError)as e:
        print('ctclab-prefix: '+str(e),file=sys.stderr);return 2
    finally:
        if temp:
            try:os.unlink(temp)
            except OSError:pass

if __name__=='__main__':raise SystemExit(main())
