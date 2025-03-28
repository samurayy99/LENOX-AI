from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from pytubefix import Search, Channel, YouTube
from langchain.tools import tool
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class VideoInfo:
    title: str
    url: str
    channel: str
    publish_date: datetime
    transcript: Optional[str] = None
    views: int = 0
    likes: int = 0

# Vordefinierte Liste von vertrauenswürdigen Solana-Influencern
TRUSTED_INFLUENCERS = {
    "Altcoin Daily": "https://www.youtube.com/@AltcoinDaily",
    "InvestAnswers": "https://www.youtube.com/@InvestAnswers",
    "CryptosRUs": "https://www.youtube.com/@CryptosRUs",
    "Coin Bureau": "https://www.youtube.com/@CoinBureau",
    "BitBoy Crypto": "https://www.youtube.com/@BitBoy_Crypto",
    "OrangieWEB3": "https://www.youtube.com/@OrangieWEB3",
    "insydercrypto": "https://www.youtube.com/@insydercrypto",
    "thefinancevalueguy": "https://www.youtube.com/@thefinancevalueguy",
    "leensx100": "https://www.youtube.com/@leensx100",
    "VicLaranja": "https://www.youtube.com/@VicLaranja",
    "CryptoBanterGroup": "https://www.youtube.com/@CryptoBanterGroup"
}

def is_recent_video(video, max_age_hours: int = 72) -> bool:
    """
    Überprüft, ob ein Video innerhalb der letzten X Stunden veröffentlicht wurde.
    
    Args:
        video: Das YouTube-Video-Objekt
        max_age_hours: Maximales Alter in Stunden (Standard: 72 Stunden)
        
    Returns:
        bool: True, wenn das Video innerhalb des angegebenen Zeitraums veröffentlicht wurde
    """
    try:
        # Manchmal ist publish_date None oder kein datetime-Objekt
        if not video.publish_date:
            # Wenn kein Datum vorhanden, nehmen wir es trotzdem mit - besser als nichts
            logger.warning(f"Video ohne Publish-Date gefunden: {video.title}, nehme es trotzdem mit")
            return True
        
        if not isinstance(video.publish_date, datetime):
            # Versuche Konvertierung wenn möglich
            try:
                if isinstance(video.publish_date, str):
                    from dateutil import parser
                    publish_date = parser.parse(video.publish_date)
                    
                    # Berechne das Zeitlimit
                    time_limit = datetime.now() - timedelta(hours=max_age_hours)
                    return publish_date > time_limit
            except:
                # Bei Fehlern nehmen wir es mit
                logger.warning(f"Datum konnte nicht konvertiert werden: {video.publish_date}, nehme Video trotzdem mit")
                return True
        else:
            # Berechne das Zeitlimit
            time_limit = datetime.now() - timedelta(hours=max_age_hours)
            
            # Korrektur für YouTube-API Datumsformat
            # Manchmal sind die Zeitzonen falsch - wir sind großzügig
            # und geben 12 Stunden extra Spielraum
            time_limit = time_limit - timedelta(hours=12)
            
            # Vergleiche das Veröffentlichungsdatum mit dem Zeitlimit
            return video.publish_date > time_limit
        
        # Im Zweifel nehmen wir das Video mit (lieber zu viel als zu wenig)
        return True
        
    except Exception as e:
        logger.error(f"Fehler bei der Überprüfung des Veröffentlichungsdatums: {e}")
        # Im Fehlerfall nehmen wir das Video mit (lieber zu viel als zu wenig)
        return True

def extract_transcript(video_url: str) -> Optional[str]:
    """
    Extrahiert das Transkript aus einem YouTube-Video.
    Verwendet die offizielle Pytubefix API für Caption-Extraktion.
    """
    try:
        yt = YouTube(video_url)
        
        # Versuche die verschiedenen Caption-Typen
        caption_types = ['a.en', 'en', 'en-GB', 'en-US']
        
        for caption_type in caption_types:
            try:
                if caption_type in yt.captions:
                    caption = yt.captions[caption_type]
                    try:
                        # Versuche zuerst die SRT-Format
                        return caption.generate_srt_captions()
                    except Exception as e:
                        logger.warning(f"SRT-Format fehlgeschlagen: {e}")
                        # Wenn SRT fehlschlägt, versuche XML
                        try:
                            return caption.xml_captions
                        except Exception as e:
                            logger.warning(f"XML-Format fehlgeschlagen: {e}")
                            # Als letzter Ausweg: Speichere in Datei und lese
                            try:
                                caption.save_captions("temp_captions.txt")
                                with open("temp_captions.txt", "r") as f:
                                    return f.read()
                            except Exception as e:
                                logger.warning(f"Datei-Speichern fehlgeschlagen: {e}")
            except Exception as e:
                logger.debug(f"Fehler bei Caption-Typ {caption_type}: {e}")
                continue
        
        # Wenn keine englischen Captions gefunden wurden, versuche die erste verfügbare
        if yt.captions:
            try:
                first_caption = list(yt.captions.values())[0]
                return first_caption.generate_srt_captions()
            except Exception as e:
                logger.warning(f"Erste verfügbare Caption fehlgeschlagen: {e}")
        
        return None
        
    except Exception as e:
        logger.error(f"Fehler beim Extrahieren des Transkripts: {e}")
        return None

@tool
def get_token_youtube_alpha(token_symbol: str) -> str:
    """
    Analysiert YouTube-Videos zu einem Token und fasst die Ergebnisse zusammen.

    Args:
        token_symbol: Das Token-Symbol (z.B. "WIF", "SOL", "BONK")

    Returns:
        Eine Zusammenfassung der relevanten Videos zum Token
    """
    try:
        # Bereinige den Token-Symbol
        token_symbol = token_symbol.strip().upper().replace("$", "")
        
        # Nur eine einfache Suche durchführen, um Geschwindigkeit zu erhöhen
        search_query = f"{token_symbol} token crypto"
        
        # Führe Suche durch, begrenzt auf wenige Ergebnisse für Geschwindigkeit
        results = Search(search_query)
        videos = list(results.videos)[:10]  # Nur die ersten 10 Videos

        if not videos:
            return f"🔍 Keine Videos zu ${token_symbol} gefunden."
            
        # Sammle Informationen ohne aufwändige Transkript-Analyse
        all_videos_info = []
        
        for video in videos:
            try:
                # Grundlegende Informationen sammeln, ohne Transkripte zu extrahieren
                video_info = {
                    "title": video.title if video.title else "Unbekannter Titel",
                    "url": video.watch_url,
                    "channel": video.author if video.author else "Unbekannter Kanal",
                    "views": int(video.views) if video.views is not None else 0,
                    "description": video.description if hasattr(video, "description") else ""
                }
                
                all_videos_info.append(video_info)
                
            except Exception as e:
                logger.error(f"Fehler bei Video-Verarbeitung: {e}")
                continue
        
        if not all_videos_info:
            return f"📹 Keine analysierbaren Videos für ${token_symbol} gefunden."
            
        # Erstelle eine prägnante Zusammenfassung
        summary = f"🔥 ${token_symbol} auf YouTube:\n\n"
        
        # Zeige Top-Videos basierend auf Views
        sorted_videos = sorted(all_videos_info, key=lambda x: x.get('views', 0), reverse=True)
        
        summary += "📊 Top Videos:\n"
        for idx, video in enumerate(sorted_videos[:3], 1):
            views_str = f"{video.get('views', 0):,}".replace(",", ".")
            
            summary += f"{idx}. \"{video['title']}\"\n"
            summary += f"   👁️ {views_str} Views | 👤 {video['channel']}\n"
            summary += f"   🔗 {video['url']}\n\n"
        
        # Schlusswort
        summary += f"💡 Diese Videos enthalten aktuelle Informationen zu ${token_symbol}. Für tiefere Analysen kann eine detaillierte Auswertung durchgeführt werden."
        
        return summary
        
    except Exception as e:
        logger.error(f"Fehler bei YouTube-Analyse für ${token_symbol}: {str(e)}")
        return f"⚠️ Fehler bei YouTube-Analyse für ${token_symbol}: {str(e)}"

@tool
def get_influencer_youtube_alpha(query: str = "latest") -> str:
    """
    Zeigt die neuesten Videos von vordefinierten Solana-Influencern.

    Args:
        query: Optional. Suchbegriff für spezifische Themen (Standard: "latest")

    Returns:
        Eine Zusammenfassung der neuesten Influencer-Videos
    """
    try:
        # Begrenzen auf wenige Influencer für schnellere Ergebnisse
        top_influencers = {k: v for k, v in list(TRUSTED_INFLUENCERS.items())[:5]}
        
        all_videos = []
        checked_influencers = 0
        
        # Beschränke auf maximal 5 Influencer für Performance
        for influencer_name, channel_url in top_influencers.items():
            try:
                checked_influencers += 1
                channel = Channel(channel_url)
                
                # Hole maximal 3 neueste Videos pro Kanal für bessere Geschwindigkeit
                videos = list(channel.videos)[:3]
                
                for video in videos:
                    try:
                        # Nur grundlegende Informationen sammeln
                        video_info = {
                            "title": video.title if video.title else "Unbekannter Titel",
                            "url": video.watch_url,
                            "channel": influencer_name,
                            "views": int(video.views) if video.views is not None else 0
                        }
                        
                        # Wenn Query vorhanden ist, prüfe ob im Titel enthalten
                        if query.lower() != "latest":
                            if query.lower() not in video.title.lower():
                                continue
                        
                        all_videos.append(video_info)
                        
                    except Exception as e:
                        logger.error(f"Fehler bei Video: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Fehler bei Channel {influencer_name}: {e}")
                continue
        
        # Erstelle eine kompakte Zusammenfassung
        summary = "🔥 SOLANA INFLUENCER UPDATES 🔥\n\n"
        
        # Statistik zur Übersicht
        summary += f"📊 Stats: {checked_influencers} Influencer gecheckt, {len(all_videos)} neueste Videos gefunden\n\n"
        
        # Wenn keine Videos gefunden wurden
        if not all_videos:
            summary += "😴 Keine passenden Videos gefunden."
            return summary
        
        # Sortiere nach Views (höchste zuerst)
        sorted_videos = sorted(all_videos, key=lambda x: x.get('views', 0), reverse=True)
        
        # Zeige die Top-Videos
        for idx, video in enumerate(sorted_videos[:5], 1):
            views_str = f"{video.get('views', 0):,}".replace(",", ".")
            
            summary += f"{idx}. 👤 {video['channel']}\n"
            summary += f"   📺 {video['title']}\n"
            summary += f"   👁️ {views_str} Views\n"
            summary += f"   🔗 {video['url']}\n\n"
        
        return summary
        
    except Exception as e:
        logger.error(f"Fehler beim Sammeln der Influencer-Videos: {str(e)}")
        return f"⚠️ Fehler beim Sammeln der Influencer-Videos: {str(e)}"

@tool
def scan_youtube_for_alpha(keyword: str = "solana") -> str:
    """
    Scannt YouTube nach aktuellen Alpha-Signalen zu einem Keyword.

    Args:
        keyword: Suchbegriff (Standard: "solana")

    Returns:
        Eine Übersicht aktueller Alpha-Videos
    """
    try:
        # Alpha-bezogene Suchbegriffe
        search_query = f"{keyword} crypto alpha"
        
        # Führe eine einzelne Suche durch (für Geschwindigkeit)
        results = Search(search_query)
        videos = list(results.videos)[:10]  # Begrenze auf 10 Videos
        
        # Filtere Videos mit zuwenig Views
        min_views = 100
        
        # Sammle Video-Informationen
        alpha_videos = []
        
        for video in videos:
            try:
                # Nur Basis-Informationen extrahieren
                views = int(video.views) if video.views is not None else 0
                
                # Ignoriere Videos mit zu wenig Views
                if views < min_views:
                    continue
                    
                video_info = {
                    "title": video.title,
                    "url": video.watch_url,
                    "channel": video.author,
                    "views": views
                }
                
                alpha_videos.append(video_info)
                
            except Exception as e:
                logger.error(f"Fehler bei Video-Verarbeitung: {e}")
                continue
                
        if not alpha_videos:
            return f"🔍 Keine relevanten Alpha-Videos zu '{keyword}' gefunden."
            
        # Erstelle eine übersichtliche Zusammenfassung
        summary = f"🔍 ALPHA-SCANNER: '{keyword.upper()}'\n\n"
        
        # Stats
        summary += f"Gefunden: {len(alpha_videos)} relevante Videos\n\n"
        
        # Sortiere nach Views
        sorted_videos = sorted(alpha_videos, key=lambda x: x.get('views', 0), reverse=True)
        
        for idx, video in enumerate(sorted_videos[:5], 1):
            views_str = f"{video.get('views', 0):,}".replace(",", ".")
            
            summary += f"{idx}. \"{video['title']}\"\n"
            summary += f"   👤 {video['channel']} | 👁️ {views_str} Views\n"
            summary += f"   🔗 {video['url']}\n\n"
            
        summary += "💡 Diese Videos könnten wichtige Alpha-Signale enthalten."
        
        return summary
        
    except Exception as e:
        logger.error(f"Fehler beim Alpha-Scan: {str(e)}")
        return f"⚠️ Fehler beim Alpha-Scan: {str(e)}"