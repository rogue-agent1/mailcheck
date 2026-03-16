#!/usr/bin/env python3
"""mailcheck - Check IMAP inbox for new messages."""
import imaplib, email, argparse, sys, json, os
from email.header import decode_header

def decode_subject(subject):
    parts = decode_header(subject)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or 'utf-8', errors='replace'))
        else:
            decoded.append(part)
    return ''.join(decoded)

def main():
    p = argparse.ArgumentParser(description='IMAP inbox checker')
    p.add_argument('--host', required=True, help='IMAP server')
    p.add_argument('--port', type=int, default=993)
    p.add_argument('--user', required=True)
    p.add_argument('--password', help='Password (or set MAIL_PASSWORD env)')
    p.add_argument('-n', '--count', type=int, default=10, help='Messages to show')
    p.add_argument('--unseen', action='store_true', help='Unseen only')
    p.add_argument('--folder', default='INBOX')
    p.add_argument('-j', '--json', action='store_true')
    args = p.parse_args()

    password = args.password or os.environ.get('MAIL_PASSWORD')
    if not password:
        print("Set --password or MAIL_PASSWORD env"); sys.exit(1)

    try:
        mail = imaplib.IMAP4_SSL(args.host, args.port)
        mail.login(args.user, password)
        mail.select(args.folder, readonly=True)
        
        criteria = 'UNSEEN' if args.unseen else 'ALL'
        _, data = mail.search(None, criteria)
        ids = data[0].split()
        
        if not ids:
            print("No messages."); return
        
        recent_ids = ids[-args.count:]
        messages = []
        
        for mid in reversed(recent_ids):
            _, msg_data = mail.fetch(mid, '(RFC822.HEADER)')
            msg = email.message_from_bytes(msg_data[0][1])
            messages.append({
                'id': mid.decode(),
                'from': msg.get('From', ''),
                'subject': decode_subject(msg.get('Subject', '')),
                'date': msg.get('Date', ''),
            })
        
        if args.json:
            print(json.dumps(messages, indent=2))
        else:
            for m in messages:
                print(f"  {m['date'][:25]:<27} {m['from'][:30]:<32} {m['subject'][:50]}")
            print(f"\n  {len(ids)} total, showing {len(messages)}")
        
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr); sys.exit(1)

if __name__ == '__main__':
    main()
