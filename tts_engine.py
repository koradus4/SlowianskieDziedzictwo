"""
Moduł TTS - Piper Text-to-Speech
"""

import subprocess
import os
from pathlib import Path
import uuid
import re
import wave


class TTSEngine:
    """Silnik TTS oparty na Piper"""
    
    def __init__(self, podcast_dir: Path):
        self.podcast_dir = Path(podcast_dir)
        self.piper_exe = self.podcast_dir / "piper" / "piper.exe"
        self.espeak_data = self.podcast_dir / "piper" / "espeak-ng-data"
        self.voices_dir = self.podcast_dir / "voices"
        
        # Ścieżki do głosów
        self.glosy = {
            "jarvis": self.voices_dir / "jarvis" / "pl_PL-jarvis_wg_glos-medium.onnx",
            "meski": self.voices_dir / "meski" / "pl_PL-meski_wg_glos-medium.onnx",
            "zenski": self.voices_dir / "zenski" / "pl_PL-zenski_wg_glos-medium.onnx",
            "justyna": self.voices_dir / "justyna" / "pl_PL-justyna_wg_glos-medium.onnx",
            "darkman": self.voices_dir / "darkman" / "pl_PL-darkman-medium.onnx"
        }
        
        # Katalog na audio
        self.audio_dir = Path(__file__).parent / "audio"
        self.audio_dir.mkdir(exist_ok=True)
    
    def syntezuj(self, tekst: str, glos: str = "jarvis") -> Path:
        """Syntezuje tekst do pliku audio"""
        if not self.piper_exe.exists():
            print(f"Brak piper.exe: {self.piper_exe}")
            return None
            
        model_path = self.glosy.get(glos)
        if not model_path or not model_path.exists():
            print(f"Brak modelu głosu: {glos}")
            return None
        
        # Unikalny plik wyjściowy
        output_file = self.audio_dir / f"{uuid.uuid4().hex}.wav"
        
        try:
            cmd = [
                str(self.piper_exe),
                "--model", str(model_path),
                "--data-dir", str(self.espeak_data),
                "--output_file", str(output_file)
            ]
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            stdout, stderr = process.communicate(input=tekst.encode('utf-8'), timeout=60)
            
            if process.returncode == 0 and output_file.exists():
                return output_file
            else:
                print(f"Błąd TTS: {stderr.decode('utf-8', errors='ignore')[:100]}")
                return None
                
        except Exception as e:
            print(f"Błąd syntezy: {e}")
            return None
    
    def dostepne_glosy(self) -> list:
        """Zwraca listę dostępnych głosów"""
        return [g for g, p in self.glosy.items() if p.exists()]
    
    def syntezuj_multi_voice(self, tekst: str, plec_gracza: str = "mezczyzna") -> Path:
        """
        Syntezuje tekst z wieloma głosami dla różnych postaci.
        Format tekstu: **Narrator:** tekst, **Gracz:** tekst, **NPC [M/K]:** tekst
        """
        # Parsuj tekst na segmenty z głosami
        segments = self._parsuj_dialogi(tekst, plec_gracza)
        
        if not segments:
            # Fallback - cały tekst jako narrator
            return self.syntezuj(tekst, "jarvis")
        
        # Generuj audio dla każdego segmentu
        audio_files = []
        for speaker, text in segments:
            if text.strip():
                audio_path = self.syntezuj(text, speaker)
                if audio_path:
                    audio_files.append(audio_path)
        
        if not audio_files:
            return None
        
        # Jeśli tylko jeden plik, zwróć go
        if len(audio_files) == 1:
            return audio_files[0]
        
        # Sklej wszystkie pliki WAV
        return self._sklej_audio(audio_files)
    
    def _parsuj_dialogi(self, tekst: str, plec_gracza: str) -> list:
        """
        Parsuje tekst i zwraca listę (głos, tekst).
        Format: **Mówca:** tekst lub **Mówca [M/K]:** tekst
        """
        segments = []
        
        # Regex: **cokolwiek:** dowolny tekst (do następnego ** lub końca)
        pattern = r'\*\*([^:]+):\*\*\s*([^*]+?)(?=\*\*|$)'
        matches = re.findall(pattern, tekst, re.DOTALL)
        
        for speaker_raw, text in matches:
            speaker = speaker_raw.strip()
            text = text.strip()
            
            # Określ głos
            voice = self._okresl_glos(speaker, plec_gracza)
            segments.append((voice, text))
        
        return segments
    
    def _okresl_glos(self, speaker: str, plec_gracza: str) -> str:
        """Wymusza użycie jednego głosu (jarvis) dla całej narracji."""
        # Upraszczamy: niezależnie od mówiącego zwracamy jarvis, by uniknąć braków modeli
        return 'jarvis'
    
    def _sklej_audio(self, audio_files: list) -> Path:
        """Skleja wiele plików WAV w jeden"""
        output_file = self.audio_dir / f"{uuid.uuid4().hex}.wav"
        
        try:
            # Otwórz wszystkie pliki i zbierz dane
            data = []
            params = None
            
            for audio_path in audio_files:
                with wave.open(str(audio_path), 'rb') as wf:
                    if params is None:
                        params = wf.getparams()
                    data.append(wf.readframes(wf.getnframes()))
            
            # Zapisz sklejony plik
            with wave.open(str(output_file), 'wb') as output:
                output.setparams(params)
                for d in data:
                    output.writeframes(d)
            
            # Usuń tymczasowe pliki
            for audio_path in audio_files:
                try:
                    audio_path.unlink()
                except:
                    pass
            
            return output_file
            
        except Exception as e:
            print(f"Błąd sklejania audio: {e}")
            # Zwróć pierwszy plik jako fallback
            return audio_files[0] if audio_files else None
