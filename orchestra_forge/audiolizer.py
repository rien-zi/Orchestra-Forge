"""Local Audiolizer: a visual General MIDI instrument playground."""
from __future__ import annotations
import argparse
from collections import OrderedDict
import json
import math
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import webbrowser

from orchestra_forge.composition import Composition, Note, Part
from orchestra_forge.midi import write_midi

ROOT = Path(__file__).resolve().parent
NAMES = '''Acoustic Grand Piano|Bright Acoustic Piano|Electric Grand Piano|Honky-tonk Piano|Electric Piano 1|Electric Piano 2|Harpsichord|Clavinet|Celesta|Glockenspiel|Music Box|Vibraphone|Marimba|Xylophone|Tubular Bells|Dulcimer|Drawbar Organ|Percussive Organ|Rock Organ|Church Organ|Reed Organ|Accordion|Harmonica|Tango Accordion|Nylon Guitar|Steel Guitar|Jazz Guitar|Clean Electric Guitar|Muted Electric Guitar|Overdriven Guitar|Distortion Guitar|Guitar Harmonics|Acoustic Bass|Fingered Bass|Picked Bass|Fretless Bass|Slap Bass 1|Slap Bass 2|Synth Bass 1|Synth Bass 2|Violin|Viola|Cello|Contrabass|Tremolo Strings|Pizzicato Strings|Orchestral Harp|Timpani|String Ensemble 1|String Ensemble 2|Synth Strings 1|Synth Strings 2|Choir Aahs|Voice Oohs|Synth Voice|Orchestra Hit|Trumpet|Trombone|Tuba|Muted Trumpet|French Horn|Brass Section|Synth Brass 1|Synth Brass 2|Soprano Sax|Alto Sax|Tenor Sax|Baritone Sax|Oboe|English Horn|Bassoon|Clarinet|Piccolo|Flute|Recorder|Pan Flute|Blown Bottle|Shakuhachi|Whistle|Ocarina|Square Lead|Sawtooth Lead|Calliope Lead|Chiff Lead|Charang Lead|Voice Lead|Fifths Lead|Bass and Lead|New Age Pad|Warm Pad|Polysynth Pad|Choir Pad|Bowed Pad|Metallic Pad|Halo Pad|Sweep Pad|Rain FX|Soundtrack FX|Crystal FX|Atmosphere FX|Brightness FX|Goblins FX|Echoes FX|Sci-fi FX|Sitar|Banjo|Shamisen|Koto|Kalimba|Bagpipe|Fiddle|Shanai|Tinkle Bell|Agogo|Steel Drums|Woodblock|Taiko Drum|Melodic Tom|Synth Drum|Reverse Cymbal|Guitar Fret Noise|Breath Noise|Seashore|Bird Tweet|Telephone Ring|Helicopter|Applause|Gunshot'''.split('|')


def number(data, key, low, high, integer=False):
    value=data.get(key)
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high or (integer and not isinstance(value,int)):
        raise ValueError(f'{key} must be {"an integer " if integer else ""}between {low} and {high}')
    return value


class PreviewEngine:
    def __init__(self, soundfont):
        self.soundfont=soundfont
        self.cache=OrderedDict()
        self.lock=threading.Lock()
        self.slots=threading.BoundedSemaphore(2)

    def preview(self, data):
        program=number(data,'program',0,127,True)
        pitch=number(data,'pitch',24,96,True)
        velocity=number(data,'velocity',1,100,True)
        duration=number(data,'duration',.2,3)
        pattern=data.get('pattern','note')
        intervals={'note':(0,), 'chord':(0,4,7), 'phrase':(0,2,4,7,4,2,0)}
        if pattern not in intervals:
            raise ValueError('Unknown preview pattern')
        if pitch+max(intervals[pattern])>127:
            raise ValueError('Phrase exceeds MIDI range')
        key=(program,pitch,velocity,duration,pattern)
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
        if not self.slots.acquire(blocking=False):
            raise RuntimeError('A preview is already rendering. Try again in a moment.')
        try:
            notes=tuple(Note(i*duration if pattern=='phrase' else 0,duration,pitch+offset,velocity)
                        for i,offset in enumerate(intervals[pattern]))
            beats=duration*len(notes) if pattern=='phrase' else duration
            score=Composition('Audiolizer preview',60,beats,(Part(NAMES[program],program,0,notes),))
            with tempfile.TemporaryDirectory(prefix='orchestra-audiolizer-') as temp:
                midi=Path(temp)/'preview.mid'; wav=Path(temp)/'preview.wav'
                write_midi(midi,score)
                subprocess.run(['fluidsynth','-ni','-g','0.4','-C','0','-R','1',
                                '-o','synth.reverb.room-size=0.5','-o','synth.reverb.level=0.14',
                                '-o','synth.reverb.damp=0.55','-r','44100','-T','wav','-O','s16',
                                '-F',str(wav),str(self.soundfont),str(midi)],
                               check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=30)
                audio=wav.read_bytes()
            with self.lock:
                self.cache[key]=audio
                while len(self.cache)>16:
                    self.cache.popitem(last=False)
            return audio
        finally:
            self.slots.release()


def handler(engine):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def respond(self,status,payload,kind='application/json'):
            if isinstance(payload,dict):
                payload=json.dumps(payload).encode()
            self.send_response(status)
            self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(payload)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            try:
                self.wfile.write(payload)
            except (BrokenPipeError,ConnectionResetError):
                pass

        def do_GET(self):
            path=self.path.split('?')[0]
            if path=='/api/instruments':
                return self.respond(200,{'instruments':[{'program':i,'name':name} for i,name in enumerate(NAMES)],'soundfont':engine.soundfont.name})
            assets={'/':('index.html','text/html; charset=utf-8'), '/style.css':('style.css','text/css'), '/app.js':('app.js','text/javascript')}
            if path not in assets:
                return self.respond(404,{'error':'Not found'})
            name,kind=assets[path]
            self.respond(200,(ROOT/'web'/name).read_bytes(),kind)

        def do_POST(self):
            if self.path!='/api/preview':
                return self.respond(404,{'error':'Not found'})
            origin=self.headers.get('Origin')
            allowed={f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}
            if origin and origin not in allowed:
                return self.respond(403,{'error':'Only local Audiolizer requests are accepted'})
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':
                return self.respond(415,{'error':'Expected JSON'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=4096:
                    raise ValueError('Invalid request size')
                data=json.loads(self.rfile.read(length))
                if not isinstance(data,dict):
                    raise ValueError('Expected an object')
                audio=engine.preview(data)
                self.respond(200,audio,'audio/wav')
            except (ValueError,TypeError) as exc:
                self.respond(400,{'error':str(exc)})
            except RuntimeError as exc:
                self.respond(429,{'error':str(exc)})
            except (OSError,subprocess.SubprocessError):
                self.respond(500,{'error':'Preview rendering failed. Check FluidSynth and your SoundFont.'})
    return Handler


def main(argv=None):
    parser=argparse.ArgumentParser(description='Open the local Audiolizer instrument playground.')
    parser.add_argument('--soundfont',type=Path,default=Path(os.environ.get('ORCHESTRA_FORGE_SOUNDFONT',str(Path.cwd()/'soundfonts'/'GeneralUser GS v1.471.sf2'))))
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--no-open',action='store_true')
    args=parser.parse_args(argv)
    if not shutil.which('fluidsynth'):
        parser.error('FluidSynth is not installed or not on PATH')
    if not args.soundfont.is_file():
        parser.error('SoundFont not found. Provide --soundfont /path/to/library.sf2')
    if not 1024<=args.port<=65535:
        parser.error('Port must be between 1024 and 65535')
    try:
        server=ThreadingHTTPServer(('127.0.0.1',args.port),handler(PreviewEngine(args.soundfont.resolve())))
    except OSError as exc:
        parser.error(f'Cannot open port {args.port}: {exc}. Try --port 8766')
    server.daemon_threads=True
    url=f'http://127.0.0.1:{args.port}'
    print(f'Audiolizer: {url}\nPress Ctrl+C to stop.',flush=True)
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__=='__main__':
    main()
