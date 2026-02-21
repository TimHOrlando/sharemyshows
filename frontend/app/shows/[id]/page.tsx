'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import Navbar from '@/components/Navbar';
import SettingsModal from '@/components/SettingsModal';
import { api } from '@/lib/api';
import { io, Socket } from 'socket.io-client';

interface Song {
  id?: number;
  position?: number;
  order?: number;
  song_name?: string;
  title?: string;
  notes?: string;
  is_cover?: boolean;
  original_artist?: string;
  duration?: string;
  songwriter?: string;
  with_artist?: string;
}

interface Photo {
  id: number;
  filename: string;
  caption?: string;
  comment_count?: number;
  created_at: string;
}

interface Video {
  id: number;
  user_id: number;
  show_id: number;
  filename: string;
  original_filename?: string;
  title?: string;
  description?: string;
  duration?: number;
  file_size?: number;
  created_at: string;
  url: string;
  thumbnail_url?: string | null;
}

interface Comment {
  id: number;
  show_id: number;
  photo_id?: number;
  user: { id: number; username: string; email: string };
  text: string;
  created_at: string;
  updated_at?: string;
}

interface Show {
  id: number;
  date: string;
  show_date?: string;
  time?: string;
  venue?: { id: number; name: string; city?: string; state?: string; address?: string };
  venue_name?: string;
  city?: string;
  state?: string;
  notes?: string;
  rating?: number;
  is_live?: boolean;
  is_owner?: boolean;
  owner?: { id: number; username: string };
  artist?: { id: number; name: string };
  artists?: { id: number; name: string }[];
  setlist?: Song[];
  photos?: Photo[];
  videos?: Video[];
  comments?: Comment[];
  photo_count?: number;
  video_count?: number;
  audio_count?: number;
  song_count?: number;
  comment_count?: number;
}

interface NearbyUser {
  id: number;
  username: string;
  distance?: string;
  last_seen: string;
  is_friend: boolean;
}

export default function ShowDetailPage() {
  const params = useParams();
  const router = useRouter();
  const showId = params.id as string;

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [show, setShow] = useState<Show | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'setlist' | 'photos' | 'videos' | 'comments' | 'people'>('setlist');

  // Setlist state
  const [newSongName, setNewSongName] = useState('');
  const [showSongDetails, setShowSongDetails] = useState(false);
  const [newSongCover, setNewSongCover] = useState(false);
  const [newSongOriginalArtist, setNewSongOriginalArtist] = useState('');
  const [newSongDuration, setNewSongDuration] = useState('');
  const [newSongSongwriter, setNewSongSongwriter] = useState('');
  const [newSongWithArtist, setNewSongWithArtist] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [shazamResult, setShazamResult] = useState<string | null>(null);

  // Edit/delete state
  const [isEditing, setIsEditing] = useState(false);
  const [editNotes, setEditNotes] = useState('');
  const [editRating, setEditRating] = useState<number | null>(null);
  const [, setIsDeleting] = useState(false);

  // Photo state
  const [isUploading, setIsUploading] = useState(false);
  const [photoCaption, setPhotoCaption] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Photo modal state
  const [selectedPhoto, setSelectedPhoto] = useState<Photo | null>(null);
  const [photoComments, setPhotoComments] = useState<Comment[]>([]);
  const [newPhotoComment, setNewPhotoComment] = useState('');

  // Video state
  const [isVideoUploading, setIsVideoUploading] = useState(false);
  const [videoUploadProgress, setVideoUploadProgress] = useState(0);
  const [videoTitle, setVideoTitle] = useState('');
  const videoFileInputRef = useRef<HTMLInputElement>(null);

  // Video recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [recordedPreviewUrl, setRecordedPreviewUrl] = useState<string | null>(null);
  const [showRecordingUI, setShowRecordingUI] = useState(false);
  const [recordingError, setRecordingError] = useState<string | null>(null);
  const videoPreviewRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  // Video playback modal
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);

  // Comments state
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');

  // People/presence state
  const [nearbyUsers, setNearbyUsers] = useState<NearbyUser[]>([]);
  const [, setLocationEnabled] = useState(false);
  const [sharingLocation, setSharingLocation] = useState(false);

  // WebSocket
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    if (showId) {
      fetchShow();

      // If auto-setlist was requested, re-fetch after a delay to pick up populated songs
      const params = new URLSearchParams(window.location.search);
      if (params.get('autoSetlist')) {
        const timer = setTimeout(() => fetchShow(), 2500);
        return () => clearTimeout(timer);
      }
    }
  }, [showId]);

  // WebSocket connection
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token || !showId) return;

    const socket = io(process.env.NEXT_PUBLIC_API_URL?.replace('/api', '') || 'http://localhost:5000', {
      query: { token },
      transports: ['websocket', 'polling'],
    });

    socket.on('connect', () => {
      socket.emit('join_show', { show_id: parseInt(showId) });
    });

    socket.on('comment_added', (data: { show_id: number; photo_id?: number; comment: Comment }) => {
      if (data.photo_id) {
        // Photo comment - update if that photo modal is open
        if (selectedPhoto && selectedPhoto.id === data.photo_id) {
          setPhotoComments(prev => [...prev, data.comment]);
        }
      } else {
        // Show comment
        setComments(prev => [...prev, data.comment]);
      }
    });

    socketRef.current = socket;

    return () => {
      socket.emit('leave_show', { show_id: parseInt(showId) });
      socket.disconnect();
      socketRef.current = null;
    };
  }, [showId]);

  const fetchShow = async () => {
    try {
      const response = await api.get(`/shows/${showId}`);
      setShow(response.data);
      setComments(response.data.comments || []);
    } catch (error) {
      console.error('Failed to fetch show:', error);
    } finally {
      setLoading(false);
    }
  };

  // Setlist functions
  const addSong = async () => {
    if (!newSongName.trim() || !show) return;

    try {
      const position = (show.setlist?.length || 0) + 1;
      const payload: Record<string, unknown> = {
        song_name: newSongName.trim(),
        position,
      };
      if (newSongCover) payload.is_cover = true;
      if (newSongOriginalArtist.trim()) payload.original_artist = newSongOriginalArtist.trim();
      if (newSongDuration.trim()) payload.duration = newSongDuration.trim();
      if (newSongSongwriter.trim()) payload.songwriter = newSongSongwriter.trim();
      if (newSongWithArtist.trim()) payload.with_artist = newSongWithArtist.trim();

      const response = await api.post(`/shows/${showId}/setlist`, payload);

      setShow(prev => prev ? {
        ...prev,
        setlist: [...(prev.setlist || []), response.data]
      } : null);
      setNewSongName('');
      setNewSongCover(false);
      setNewSongOriginalArtist('');
      setNewSongDuration('');
      setNewSongSongwriter('');
      setNewSongWithArtist('');
      setShowSongDetails(false);
    } catch (error) {
      console.error('Failed to add song:', error);
    }
  };

  const removeSong = async (songId: number) => {
    try {
      await api.delete(`/shows/${showId}/setlist/${songId}`);
      setShow(prev => prev ? {
        ...prev,
        setlist: (prev.setlist || []).filter(s => s.id !== songId)
      } : null);
    } catch (error) {
      console.error('Failed to remove song:', error);
    }
  };

  // Shazam-like functionality
  const startListening = async () => {
    setIsListening(true);
    setShazamResult(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setTimeout(() => {
        stream.getTracks().forEach(track => track.stop());
        setIsListening(false);
        setShazamResult('Listening complete - integrate Shazam API for song recognition');
      }, 5000);
    } catch (error) {
      console.error('Microphone access denied:', error);
      setIsListening(false);
      setShazamResult('Microphone access denied. Please enable microphone permissions.');
    }
  };

  const stopListening = () => {
    setIsListening(false);
  };

  // Photo functions
  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    try {
      for (const file of Array.from(files)) {
        const formData = new FormData();
        formData.append('photo', file);
        if (photoCaption.trim()) {
          formData.append('caption', photoCaption.trim());
        }

        const response = await api.post(`/shows/${showId}/photos`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        setShow(prev => prev ? {
          ...prev,
          photos: [...(prev.photos || []), response.data]
        } : null);
      }
      setPhotoCaption('');
    } catch (error) {
      console.error('Failed to upload photo:', error);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Photo modal
  const openPhotoModal = useCallback(async (photo: Photo) => {
    setSelectedPhoto(photo);
    setPhotoComments([]);
    setNewPhotoComment('');
    try {
      const response = await api.get(`/comments/photo/${photo.id}`);
      setPhotoComments(response.data.comments || []);
    } catch (error) {
      console.error('Failed to fetch photo comments:', error);
    }
  }, []);

  const submitPhotoComment = async () => {
    if (!newPhotoComment.trim() || !selectedPhoto) return;
    try {
      const response = await api.post('/comments', {
        photo_id: selectedPhoto.id,
        text: newPhotoComment.trim(),
      });
      setPhotoComments(prev => [...prev, response.data]);
      setNewPhotoComment('');

      // Notify via WebSocket
      if (socketRef.current) {
        socketRef.current.emit('new_comment', {
          show_id: parseInt(showId),
          photo_id: selectedPhoto.id,
          comment: response.data,
        });
      }
    } catch (error) {
      console.error('Failed to post photo comment:', error);
    }
  };

  // Show comment functions
  const submitComment = async () => {
    if (!newComment.trim()) return;
    try {
      const response = await api.post('/comments', {
        show_id: parseInt(showId),
        text: newComment.trim(),
      });
      setComments(prev => [...prev, response.data]);
      setNewComment('');

      // Notify via WebSocket
      if (socketRef.current) {
        socketRef.current.emit('new_comment', {
          show_id: parseInt(showId),
          comment: response.data,
        });
      }
    } catch (error) {
      console.error('Failed to post comment:', error);
    }
  };

  const deleteComment = async (commentId: number) => {
    try {
      await api.delete(`/comments/${commentId}`);
      setComments(prev => prev.filter(c => c.id !== commentId));
    } catch (error) {
      console.error('Failed to delete comment:', error);
    }
  };

  const deletePhotoComment = async (commentId: number) => {
    try {
      await api.delete(`/comments/${commentId}`);
      setPhotoComments(prev => prev.filter(c => c.id !== commentId));
    } catch (error) {
      console.error('Failed to delete photo comment:', error);
    }
  };

  const deletePhoto = async (photoId: number) => {
    if (!confirm('Delete this photo?')) return;
    try {
      await api.delete(`/photos/${photoId}`);
      setShow(prev => prev ? {
        ...prev,
        photos: (prev.photos || []).filter(p => p.id !== photoId)
      } : null);
      setSelectedPhoto(null);
    } catch (error) {
      console.error('Failed to delete photo:', error);
    }
  };

  // Location/presence functions
  const toggleLocationSharing = async () => {
    if (!sharingLocation) {
      try {
        const position = await new Promise<GeolocationPosition>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: true
          });
        });

        setSharingLocation(true);
        setLocationEnabled(true);

        await api.post(`/shows/${showId}/presence`, {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        });
        fetchNearbyUsers();
      } catch (error) {
        console.error('Location access denied:', error);
        setLocationEnabled(false);
      }
    } else {
      setSharingLocation(false);
      await api.delete(`/shows/${showId}/presence`);
    }
  };

  const fetchNearbyUsers = async () => {
    try {
      const response = await api.get(`/shows/${showId}/presence`);
      setNearbyUsers(response.data.users || []);
    } catch (error) {
      console.error('Failed to fetch nearby users:', error);
    }
  };

  // Video functions
  const handleVideoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsVideoUploading(true);
    setVideoUploadProgress(0);
    try {
      for (const file of Array.from(files)) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('show_id', showId);
        if (videoTitle.trim()) formData.append('title', videoTitle.trim());

        const response = await api.post('/videos', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            const percent = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
            setVideoUploadProgress(percent);
          }
        });

        setShow(prev => prev ? {
          ...prev,
          videos: [...(prev.videos || []), response.data]
        } : null);
      }
      setVideoTitle('');
    } catch (error) {
      console.error('Failed to upload video:', error);
    } finally {
      setIsVideoUploading(false);
      setVideoUploadProgress(0);
      if (videoFileInputRef.current) videoFileInputRef.current.value = '';
    }
  };

  const getRecorderMimeType = () => {
    const types = [
      'video/webm;codecs=vp9,opus',
      'video/webm;codecs=vp8,opus',
      'video/webm',
      'video/mp4',
    ];
    for (const type of types) {
      if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(type)) return type;
    }
    return 'video/webm';
  };

  const startRecording = async () => {
    setRecordingError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      streamRef.current = stream;

      if (videoPreviewRef.current) {
        videoPreviewRef.current.srcObject = stream;
      }

      const mimeType = getRecorderMimeType();
      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        const url = URL.createObjectURL(blob);
        setRecordedBlob(blob);
        setRecordedPreviewUrl(url);
        setIsRecording(false);

        if (streamRef.current) {
          streamRef.current.getTracks().forEach(t => t.stop());
          streamRef.current = null;
        }
        if (videoPreviewRef.current) {
          videoPreviewRef.current.srcObject = null;
        }
      };

      recorder.start(1000);
      setIsRecording(true);
      setRecordingTime(0);

      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          if (prev >= 59) {
            recorder.stop();
            if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
            return 60;
          }
          return prev + 1;
        });
      }, 1000);
    } catch (error) {
      console.error('Camera access denied:', error);
      setRecordingError('Camera access denied. Please enable camera and microphone permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
  };

  const saveRecording = async () => {
    if (!recordedBlob) return;

    const ext = recordedBlob.type.includes('mp4') ? 'mp4' : 'webm';
    const file = new File([recordedBlob], `recording.${ext}`, { type: recordedBlob.type });

    setIsVideoUploading(true);
    setVideoUploadProgress(0);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('show_id', showId);
      if (videoTitle.trim()) formData.append('title', videoTitle.trim());

      const response = await api.post('/videos', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
          setVideoUploadProgress(percent);
        }
      });

      setShow(prev => prev ? {
        ...prev,
        videos: [...(prev.videos || []), response.data]
      } : null);
      cancelRecording();
      setVideoTitle('');
    } catch (error) {
      console.error('Failed to save recording:', error);
    } finally {
      setIsVideoUploading(false);
      setVideoUploadProgress(0);
    }
  };

  const cancelRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    if (videoPreviewRef.current) {
      videoPreviewRef.current.srcObject = null;
    }
    if (recordedPreviewUrl) {
      URL.revokeObjectURL(recordedPreviewUrl);
    }
    setRecordedBlob(null);
    setRecordedPreviewUrl(null);
    setIsRecording(false);
    setRecordingTime(0);
    setShowRecordingUI(false);
    setRecordingError(null);
    chunksRef.current = [];
  };

  const deleteVideo = async (videoId: number) => {
    if (!confirm('Delete this video?')) return;
    try {
      await api.delete(`/videos/${videoId}`);
      setShow(prev => prev ? {
        ...prev,
        videos: (prev.videos || []).filter(v => v.id !== videoId)
      } : null);
      setSelectedVideo(null);
    } catch (error) {
      console.error('Failed to delete video:', error);
    }
  };

  const formatVideoDuration = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  // Cleanup recording resources on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
      }
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    };
  }, []);

  // Delete handler
  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this show? This cannot be undone.')) return;
    setIsDeleting(true);
    try {
      await api.delete(`/shows/${showId}`);
      router.push('/shows');
    } catch (error) {
      console.error('Failed to delete show:', error);
      alert('Failed to delete show');
    } finally {
      setIsDeleting(false);
    }
  };

  // Edit handler
  const handleSaveEdit = async () => {
    try {
      await api.put(`/shows/${showId}`, {
        notes: editNotes,
        rating: editRating
      });
      await fetchShow();
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update show:', error);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString + (dateString.length === 10 ? 'T12:00:00' : ''));
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatTimestamp = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const isOwner = show?.is_owner !== false;

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-primary">
          <Navbar onOpenSettings={() => setIsSettingsOpen(true)} />
          <div className="flex items-center justify-center h-[60vh]">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-accent"></div>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  if (!show) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-primary">
          <Navbar onOpenSettings={() => setIsSettingsOpen(true)} />
          <div className="max-w-4xl mx-auto py-12 px-4 text-center">
            <h1 className="text-2xl font-bold text-primary mb-4">Show not found</h1>
            <button onClick={() => router.back()} className="text-accent hover:underline">
              Go back
            </button>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-primary">
        <Navbar onOpenSettings={() => setIsSettingsOpen(true)} />

        <main className="max-w-4xl mx-auto py-6 px-4">
          {/* Back button */}
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-secondary hover:text-primary mb-4 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </button>

          {/* Show Header */}
          <div className="bg-secondary rounded-xl p-6 mb-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                {!isOwner && show.owner && (
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center">
                      <span className="text-xs font-bold text-accent">{show.owner.username.charAt(0).toUpperCase()}</span>
                    </div>
                    <span className="text-sm text-accent font-medium">{show.owner.username}&apos;s show</span>
                  </div>
                )}
                {show.is_live && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-red-500/20 text-red-400 text-sm font-medium mb-3">
                    <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                    LIVE NOW
                  </span>
                )}
                <h1 className="text-2xl font-bold text-primary mb-1">
                  {show.artists?.map(a => a.name).join(', ') || show.artist?.name || 'Unknown Artist'}
                </h1>
                <p className="text-secondary text-lg">
                  {show.venue?.name || show.venue_name || 'Unknown Venue'}
                </p>
                {(show.venue?.city || show.venue?.state || show.city || show.state) && (
                  <p className="text-muted text-sm">
                    {[show.venue?.city || show.city, show.venue?.state || show.state].filter(Boolean).join(', ')}
                  </p>
                )}
                <p className="text-muted text-sm mt-1">
                  {formatDate(show.date || show.show_date || '')}
                  {show.time && ` at ${show.time}`}
                </p>
                {show.rating && (
                  <div className="flex items-center gap-1 text-accent mt-2">
                    {[...Array(5)].map((_, i) => (
                      <svg key={i} className={`w-5 h-5 ${i < show.rating! ? 'fill-current' : 'stroke-current fill-none'}`} viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                  </div>
                )}
              </div>

              {/* Edit / Delete Actions - only for owner */}
              {isOwner && (
                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => { setEditNotes(show.notes || ''); setEditRating(show.rating || null); setIsEditing(true); }}
                    className="p-2 rounded-lg text-secondary hover:text-primary hover:bg-tertiary transition-colors"
                    title="Edit show"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={handleDelete}
                    className="p-2 rounded-lg text-secondary hover:text-red-400 hover:bg-red-500/10 transition-colors"
                    title="Delete show"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              )}
            </div>

            {show.notes && (
              <p className="mt-4 text-secondary text-sm border-t border-theme pt-4">{show.notes}</p>
            )}
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-6 border-b border-theme">
            {(['setlist', 'photos', 'videos', 'comments', ...(show.is_live ? ['people'] : [])] as ('setlist' | 'photos' | 'videos' | 'comments' | 'people')[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-3 font-medium text-sm transition-colors relative ${
                  activeTab === tab
                    ? 'text-accent'
                    : 'text-secondary hover:text-primary'
                }`}
              >
                {tab === 'setlist' && 'Setlist'}
                {tab === 'photos' && `Photos (${show.photos?.length || 0})`}
                {tab === 'videos' && `Videos (${show.videos?.length || 0})`}
                {tab === 'comments' && `Comments (${comments.length})`}
                {tab === 'people' && 'People Here'}
                {activeTab === tab && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent"></span>
                )}
              </button>
            ))}
          </div>

          {/* Setlist Tab */}
          {activeTab === 'setlist' && (
            <div className="space-y-4">
              {/* Add Song Form - only for owner, hide for past shows with existing setlist */}
              {isOwner && !(new Date((show.date || show.show_date || '') + 'T23:59:59') < new Date() && show.setlist && show.setlist.length > 0) && (
              <div className="bg-secondary rounded-xl p-4">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newSongName}
                    onChange={(e) => setNewSongName(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && addSong()}
                    placeholder="Add song to setlist..."
                    className="flex-1 px-4 py-3 bg-tertiary text-primary rounded-lg border border-theme focus:outline-none focus:ring-2 focus:ring-accent placeholder:text-muted"
                  />
                  <button
                    onClick={addSong}
                    disabled={!newSongName.trim()}
                    className="px-4 py-3 bg-accent text-white rounded-lg hover:opacity-90 transition-colors disabled:opacity-50"
                  >
                    Add
                  </button>
                </div>

                {/* Song details toggle */}
                <button
                  type="button"
                  onClick={() => setShowSongDetails(!showSongDetails)}
                  className="mt-2 text-xs text-muted hover:text-secondary transition-colors flex items-center gap-1"
                >
                  <svg className={`w-3 h-3 transition-transform ${showSongDetails ? 'rotate-90' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  More details
                </button>

                {showSongDetails && (
                  <div className="mt-2 space-y-2">
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="text"
                        value={newSongDuration}
                        onChange={(e) => setNewSongDuration(e.target.value)}
                        placeholder="Duration (e.g. 5:23)"
                        className="px-3 py-2 text-sm bg-tertiary text-primary rounded-lg border border-theme focus:outline-none focus:ring-2 focus:ring-accent placeholder:text-muted"
                      />
                      <input
                        type="text"
                        value={newSongWithArtist}
                        onChange={(e) => setNewSongWithArtist(e.target.value)}
                        placeholder="Guest artist"
                        className="px-3 py-2 text-sm bg-tertiary text-primary rounded-lg border border-theme focus:outline-none focus:ring-2 focus:ring-accent placeholder:text-muted"
                      />
                    </div>
                    <input
                      type="text"
                      value={newSongSongwriter}
                      onChange={(e) => setNewSongSongwriter(e.target.value)}
                      placeholder="Songwriter(s)"
                      className="w-full px-3 py-2 text-sm bg-tertiary text-primary rounded-lg border border-theme focus:outline-none focus:ring-2 focus:ring-accent placeholder:text-muted"
                    />
                    <div className="flex items-center gap-3">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={newSongCover}
                          onChange={(e) => setNewSongCover(e.target.checked)}
                          className="w-4 h-4 rounded border-theme accent-accent"
                        />
                        <span className="text-sm text-secondary">Cover song</span>
                      </label>
                      {newSongCover && (
                        <input
                          type="text"
                          value={newSongOriginalArtist}
                          onChange={(e) => setNewSongOriginalArtist(e.target.value)}
                          placeholder="Original artist"
                          className="flex-1 px-3 py-2 text-sm bg-tertiary text-primary rounded-lg border border-theme focus:outline-none focus:ring-2 focus:ring-accent placeholder:text-muted"
                        />
                      )}
                    </div>
                  </div>
                )}

                {/* Shazam-like feature - hide for past shows */}
                {show && new Date((show.date || show.show_date || '') + 'T23:59:59') >= new Date() && (
                  <div className="mt-3 pt-3 border-t border-theme">
                    <button
                      onClick={isListening ? stopListening : startListening}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                        isListening
                          ? 'bg-red-500/20 text-red-400'
                          : 'bg-tertiary text-secondary hover:text-primary'
                      }`}
                    >
                      {isListening ? (
                        <>
                          <span className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
                          Listening... Tap to stop
                        </>
                      ) : (
                        <>
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                          </svg>
                          Identify Song (Shazam)
                        </>
                      )}
                    </button>
                    {shazamResult && (
                      <p className="mt-2 text-sm text-muted">{shazamResult}</p>
                    )}
                  </div>
                )}
              </div>
              )}

              {/* Setlist */}
              {show.setlist && show.setlist.length > 0 ? (
                <div className="space-y-4">
                  {(() => {
                    const sets: { name: string; songs: { song: Song; globalIndex: number }[] }[] = [];
                    let currentSet = '';
                    show.setlist!.forEach((song, index) => {
                      const setName = song.notes?.split(';')[0]?.trim() || '';
                      if (setName !== currentSet || sets.length === 0) {
                        currentSet = setName;
                        sets.push({ name: setName, songs: [] });
                      }
                      sets[sets.length - 1].songs.push({ song, globalIndex: index });
                    });

                    return sets.map((set, setIndex) => (
                      <div key={setIndex} className="bg-secondary rounded-xl overflow-hidden">
                        {set.name && (
                          <div className="px-4 py-2.5 border-b border-theme" style={{ background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-muted))' }}>
                            <h4 className="text-sm font-bold text-white uppercase tracking-wide">
                              {set.name.replace(/:$/, '')}
                            </h4>
                          </div>
                        )}
                        {set.songs.map(({ song, globalIndex }, songIndex) => (
                          <div
                            key={song.id || globalIndex}
                            className="flex items-center gap-4 px-4 py-3 border-b border-theme last:border-b-0 hover:bg-tertiary transition-colors group"
                          >
                            <span className="w-8 h-8 flex items-center justify-center text-sm font-medium text-muted bg-tertiary rounded-full flex-shrink-0">
                              {songIndex + 1}
                            </span>
                            <div className="flex-1 min-w-0">
                              <p className="text-primary font-medium">{song.title || song.song_name}</p>
                              <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-0.5">
                                {song.is_cover && song.original_artist && (
                                  <span className="text-xs text-muted italic">
                                    cover of {song.original_artist}
                                  </span>
                                )}
                                {song.with_artist && (
                                  <span className="text-xs text-muted">
                                    w/ {song.with_artist}
                                  </span>
                                )}
                                {song.songwriter && (
                                  <span className="text-xs text-muted">
                                    written by {song.songwriter}
                                  </span>
                                )}
                              </div>
                              {song.notes && (() => {
                                const parts = song.notes.split(';').slice(1).map(s => s.trim()).filter(Boolean);
                                return parts.length > 0 ? (
                                  <p className="text-xs text-muted mt-0.5">{parts.join('; ')}</p>
                                ) : null;
                              })()}
                            </div>
                            {song.duration && (
                              <span className="text-xs text-muted font-mono flex-shrink-0 mr-1">
                                {song.duration}
                              </span>
                            )}
                            {isOwner && (
                              <button
                                onClick={() => song.id && removeSong(song.id)}
                                className="p-2 text-muted hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0"
                              >
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    ));
                  })()}
                </div>
              ) : (
                <div className="bg-secondary rounded-xl p-8 text-center">
                  <svg className="w-12 h-12 text-muted mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                  </svg>
                  <p className="text-secondary">No songs in setlist yet</p>
                  {isOwner && <p className="text-sm text-muted mt-1">Add songs as they play!</p>}
                </div>
              )}
            </div>
          )}

          {/* Photos Tab */}
          {activeTab === 'photos' && (
            <div className="space-y-4">
              {/* Upload Section - only for owner */}
              {isOwner && (
                <div className="bg-secondary rounded-xl p-4 space-y-3">
                  <input
                    type="text"
                    value={photoCaption}
                    onChange={(e) => setPhotoCaption(e.target.value)}
                    placeholder="Add a caption..."
                    className="w-full px-4 py-2 bg-tertiary text-primary rounded-lg border border-theme focus:outline-none focus:ring-2 focus:ring-accent placeholder:text-muted text-sm"
                  />
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={handlePhotoUpload}
                    className="hidden"
                    id="photo-upload"
                  />
                  <label
                    htmlFor="photo-upload"
                    className={`flex items-center justify-center gap-2 w-full px-4 py-3 bg-tertiary text-secondary hover:text-primary rounded-lg cursor-pointer transition-colors ${
                      isUploading ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    {isUploading ? (
                      <>
                        <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                        Uploading...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        Take or Upload Photos
                      </>
                    )}
                  </label>
                </div>
              )}

              {/* Photo Grid */}
              {show.photos && show.photos.length > 0 ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {show.photos.map((photo) => (
                    <div
                      key={photo.id}
                      onClick={() => openPhotoModal(photo)}
                      className="aspect-square bg-secondary rounded-xl overflow-hidden relative group cursor-pointer"
                    >
                      <img
                        src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api'}/photos/${photo.id}/thumbnail`}
                        alt={photo.caption || 'Photo'}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.style.display = 'none';
                          target.parentElement!.querySelector('.photo-fallback')?.classList.remove('hidden');
                        }}
                      />
                      <div className="photo-fallback hidden w-full h-full flex items-center justify-center bg-tertiary absolute inset-0">
                        <svg className="w-8 h-8 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3 opacity-0 group-hover:opacity-100 transition-opacity">
                        {photo.caption && <p className="text-white text-sm">{photo.caption}</p>}
                        {(photo.comment_count ?? 0) > 0 && (
                          <p className="text-white/70 text-xs mt-1">{photo.comment_count} comment{photo.comment_count !== 1 ? 's' : ''}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-secondary rounded-xl p-8 text-center">
                  <svg className="w-12 h-12 text-muted mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <p className="text-secondary">No photos yet</p>
                  {isOwner && <p className="text-sm text-muted mt-1">Capture the moment!</p>}
                </div>
              )}
            </div>
          )}

          {/* Videos Tab */}
          {activeTab === 'videos' && (
            <div className="space-y-4">
              {/* Upload/Record Section - only for owner */}
              {isOwner && (
                <div className="bg-secondary rounded-xl p-4 space-y-3">
                  <input
                    type="text"
                    value={videoTitle}
                    onChange={(e) => setVideoTitle(e.target.value)}
                    placeholder="Video title (optional)"
                    className="w-full px-4 py-2 bg-tertiary text-primary rounded-lg border border-theme focus:outline-none focus:ring-2 focus:ring-accent placeholder:text-muted text-sm"
                  />

                  {/* Upload progress bar */}
                  {isVideoUploading && (
                    <div className="w-full bg-tertiary rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full bg-accent transition-all duration-300 rounded-full"
                        style={{ width: `${videoUploadProgress}%` }}
                      />
                    </div>
                  )}

                  <input
                    ref={videoFileInputRef}
                    type="file"
                    accept="video/*"
                    onChange={handleVideoUpload}
                    className="hidden"
                    id="video-upload"
                  />

                  {!showRecordingUI && (
                    <div className="flex gap-2">
                      <label
                        htmlFor="video-upload"
                        className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-tertiary text-secondary hover:text-primary rounded-lg cursor-pointer transition-colors ${
                          isVideoUploading ? 'opacity-50 cursor-not-allowed' : ''
                        }`}
                      >
                        {isVideoUploading ? (
                          <>
                            <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                            Uploading {videoUploadProgress}%
                          </>
                        ) : (
                          <>
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                            </svg>
                            Upload Video
                          </>
                        )}
                      </label>

                      {typeof window !== 'undefined' && typeof navigator !== 'undefined' && navigator.mediaDevices && typeof MediaRecorder !== 'undefined' && (
                        <button
                          onClick={() => setShowRecordingUI(true)}
                          className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-tertiary text-secondary hover:text-primary rounded-lg transition-colors"
                        >
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                          Record Video
                        </button>
                      )}
                    </div>
                  )}

                  {/* Recording Interface */}
                  {showRecordingUI && (
                    <div className="space-y-3">
                      {/* Live viewfinder or recorded preview */}
                      {recordedPreviewUrl ? (
                        <video
                          src={recordedPreviewUrl}
                          controls
                          className="w-full rounded-lg bg-black aspect-video"
                        />
                      ) : (
                        <video
                          ref={videoPreviewRef}
                          autoPlay
                          muted
                          playsInline
                          className="w-full rounded-lg bg-black aspect-video"
                        />
                      )}

                      {/* Timer and progress */}
                      {isRecording && (
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
                              <span className={`font-mono text-lg font-bold ${recordingTime >= 50 ? 'text-red-400' : 'text-primary'}`}>
                                {Math.floor(recordingTime / 60)}:{(recordingTime % 60).toString().padStart(2, '0')}
                              </span>
                            </div>
                            <span className="text-xs text-muted">1:00 max</span>
                          </div>
                          <div className="w-full bg-tertiary rounded-full h-1.5 overflow-hidden">
                            <div
                              className={`h-full transition-all duration-1000 rounded-full ${recordingTime >= 50 ? 'bg-red-500' : 'bg-accent'}`}
                              style={{ width: `${(recordingTime / 60) * 100}%` }}
                            />
                          </div>
                        </div>
                      )}

                      {recordingError && (
                        <p className="text-red-400 text-sm">{recordingError}</p>
                      )}

                      {/* Controls */}
                      <div className="flex gap-2">
                        {!isRecording && !recordedPreviewUrl && (
                          <>
                            <button
                              onClick={startRecording}
                              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
                            >
                              <span className="w-3 h-3 bg-white rounded-full"></span>
                              Start Recording
                            </button>
                            <button
                              onClick={cancelRecording}
                              className="px-4 py-3 bg-tertiary text-secondary rounded-lg hover:text-primary transition-colors"
                            >
                              Cancel
                            </button>
                          </>
                        )}

                        {isRecording && (
                          <button
                            onClick={stopRecording}
                            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
                          >
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                              <rect x="6" y="6" width="12" height="12" rx="2" />
                            </svg>
                            Stop Recording
                          </button>
                        )}

                        {recordedPreviewUrl && (
                          <>
                            <button
                              onClick={saveRecording}
                              disabled={isVideoUploading}
                              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-accent text-white rounded-lg hover:opacity-90 transition-colors disabled:opacity-50"
                            >
                              {isVideoUploading ? (
                                <>
                                  <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                                  Saving {videoUploadProgress}%
                                </>
                              ) : (
                                'Save Recording'
                              )}
                            </button>
                            <button
                              onClick={cancelRecording}
                              disabled={isVideoUploading}
                              className="px-4 py-3 bg-tertiary text-secondary rounded-lg hover:text-primary transition-colors disabled:opacity-50"
                            >
                              Discard
                            </button>
                          </>
                        )}
                      </div>

                      {!recordedPreviewUrl && !isRecording && (
                        <p className="text-xs text-muted text-center">
                          Video recording is limited to 1 minute for copyright protection
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Video Grid */}
              {show.videos && show.videos.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {show.videos.map((video) => (
                    <div
                      key={video.id}
                      onClick={() => setSelectedVideo(video)}
                      className="bg-secondary rounded-xl overflow-hidden cursor-pointer group hover:ring-2 hover:ring-accent/50 transition-all"
                    >
                      <div className="aspect-video bg-black relative flex items-center justify-center">
                        <svg className="w-16 h-16 text-white/40 group-hover:text-white/70 transition-colors" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M8 5v14l11-7z" />
                        </svg>
                        {video.duration && (
                          <span className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-0.5 rounded">
                            {formatVideoDuration(video.duration)}
                          </span>
                        )}
                      </div>
                      <div className="p-3">
                        <p className="text-primary font-medium text-sm truncate">
                          {video.title || video.original_filename || 'Untitled'}
                        </p>
                        <p className="text-muted text-xs mt-1">{formatTimestamp(video.created_at)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-secondary rounded-xl p-8 text-center">
                  <svg className="w-12 h-12 text-muted mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <p className="text-secondary">No videos yet</p>
                  {isOwner && <p className="text-sm text-muted mt-1">Record or upload a clip!</p>}
                </div>
              )}
            </div>
          )}

          {/* Comments Tab */}
          {activeTab === 'comments' && (
            <div className="space-y-4">
              {/* Comment Input */}
              <div className="bg-secondary rounded-xl p-4">
                <div className="flex gap-2">
                  <textarea
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        submitComment();
                      }
                    }}
                    placeholder="Write a comment..."
                    rows={2}
                    className="flex-1 px-4 py-3 bg-tertiary text-primary rounded-lg border border-theme focus:outline-none focus:ring-2 focus:ring-accent placeholder:text-muted resize-none"
                  />
                  <button
                    onClick={submitComment}
                    disabled={!newComment.trim()}
                    className="px-4 py-3 bg-accent text-white rounded-lg hover:opacity-90 transition-colors disabled:opacity-50 self-end"
                  >
                    Post
                  </button>
                </div>
              </div>

              {/* Comment List */}
              {comments.length > 0 ? (
                <div className="bg-secondary rounded-xl overflow-hidden">
                  {comments.map((comment) => (
                    <div key={comment.id} className="px-4 py-3 border-b border-theme last:border-b-0 hover:bg-tertiary transition-colors group">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0">
                          <span className="text-xs font-bold text-accent">
                            {comment.user?.username?.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-primary">{comment.user?.username}</span>
                            <span className="text-xs text-muted">{formatTimestamp(comment.created_at)}</span>
                          </div>
                          <p className="text-secondary text-sm mt-0.5 whitespace-pre-wrap">{comment.text}</p>
                        </div>
                        <button
                          onClick={() => deleteComment(comment.id)}
                          className="p-1 text-muted hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0"
                          title="Delete comment"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-secondary rounded-xl p-8 text-center">
                  <svg className="w-12 h-12 text-muted mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  <p className="text-secondary">No comments yet</p>
                  <p className="text-sm text-muted mt-1">Be the first to comment!</p>
                </div>
              )}
            </div>
          )}

          {/* People Tab */}
          {activeTab === 'people' && (
            <div className="space-y-4">
              <div className="bg-secondary rounded-xl p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-primary font-medium">Share My Location</p>
                    <p className="text-sm text-muted">Let friends find you at the venue</p>
                  </div>
                  <button
                    onClick={toggleLocationSharing}
                    className={`relative w-14 h-8 rounded-full transition-colors ${
                      sharingLocation ? 'bg-accent' : 'bg-tertiary'
                    }`}
                  >
                    <span
                      className={`absolute top-1 w-6 h-6 bg-white rounded-full transition-transform ${
                        sharingLocation ? 'translate-x-7' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>

              {sharingLocation ? (
                nearbyUsers.length > 0 ? (
                  <div className="bg-secondary rounded-xl overflow-hidden">
                    <div className="px-4 py-3 border-b border-theme">
                      <h3 className="font-medium text-primary">People at this show</h3>
                    </div>
                    {nearbyUsers.map((person) => (
                      <div
                        key={person.id}
                        className="flex items-center gap-4 px-4 py-3 border-b border-theme last:border-b-0 hover:bg-tertiary transition-colors"
                      >
                        <div className="w-10 h-10 rounded-full bg-tertiary flex items-center justify-center">
                          <span className="text-sm font-medium text-primary">
                            {person.username.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div className="flex-1">
                          <p className="text-primary font-medium">{person.username}</p>
                          {person.distance && (
                            <p className="text-sm text-muted">{person.distance} away</p>
                          )}
                        </div>
                        {person.is_friend ? (
                          <span className="px-3 py-1 text-xs font-medium text-accent bg-accent/20 rounded-full">
                            Friend
                          </span>
                        ) : (
                          <button className="px-3 py-1 text-xs font-medium text-secondary hover:text-primary bg-tertiary hover:bg-hover rounded-full transition-colors">
                            Add Friend
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-secondary rounded-xl p-8 text-center">
                    <svg className="w-12 h-12 text-muted mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <p className="text-secondary">No one else here yet</p>
                    <p className="text-sm text-muted mt-1">Be the first to check in!</p>
                  </div>
                )
              ) : (
                <div className="bg-secondary rounded-xl p-8 text-center">
                  <svg className="w-12 h-12 text-muted mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  <p className="text-secondary">Enable location sharing</p>
                  <p className="text-sm text-muted mt-1">Find friends and meet others at the show</p>
                </div>
              )}

              {sharingLocation && (
                <div className="bg-secondary rounded-xl p-4">
                  <h3 className="font-medium text-primary mb-3">Find My Friends</h3>
                  <p className="text-sm text-muted mb-4">
                    Friends who are sharing their location at this show will appear here with directions to find them.
                  </p>
                  <button className="w-full px-4 py-3 bg-tertiary text-secondary hover:text-primary rounded-lg transition-colors flex items-center justify-center gap-2">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                    </svg>
                    View Friends on Map
                  </button>
                </div>
              )}
            </div>
          )}
        </main>

        {/* Edit Modal */}
        {isEditing && (
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setIsEditing(false)}>
            <div className="bg-secondary rounded-xl p-6 max-w-md w-full" onClick={(e) => e.stopPropagation()}>
              <h2 className="text-xl font-bold text-primary mb-4">Edit Show</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-secondary mb-1">Notes</label>
                  <textarea
                    value={editNotes}
                    onChange={(e) => setEditNotes(e.target.value)}
                    rows={4}
                    className="w-full px-4 py-3 bg-tertiary text-primary rounded-lg border border-theme focus:outline-none focus:ring-2 focus:ring-accent placeholder:text-muted resize-none"
                    placeholder="Add notes about this show..."
                  />
                </div>

                <div>
                  <label className="block text-sm text-secondary mb-2">Rating</label>
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        onClick={() => setEditRating(editRating === star ? null : star)}
                        className="p-1 transition-colors"
                      >
                        <svg className={`w-8 h-8 ${star <= (editRating || 0) ? 'text-accent fill-current' : 'text-muted'}`} viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setIsEditing(false)}
                  className="flex-1 px-4 py-3 bg-tertiary text-secondary rounded-lg hover:text-primary transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveEdit}
                  className="flex-1 px-4 py-3 bg-accent text-white rounded-lg hover:opacity-90 transition-colors"
                >
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Photo Detail Modal */}
        {selectedPhoto && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setSelectedPhoto(null)}>
            <div className="bg-secondary rounded-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
              {/* Modal header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-theme">
                <h3 className="font-medium text-primary">Photo</h3>
                <div className="flex items-center gap-2">
                  {isOwner && (
                    <button
                      onClick={() => deletePhoto(selectedPhoto.id)}
                      className="p-1 text-muted hover:text-red-400 transition-colors"
                      title="Delete photo"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                  <button onClick={() => setSelectedPhoto(null)} className="p-1 text-muted hover:text-primary transition-colors">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Photo */}
              <div className="flex-shrink-0">
                <img
                  src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api'}/photos/${selectedPhoto.id}`}
                  alt={selectedPhoto.caption || 'Photo'}
                  className="w-full max-h-[50vh] object-contain bg-black"
                />
              </div>

              {/* Caption */}
              {selectedPhoto.caption && (
                <div className="px-4 py-2 border-b border-theme">
                  <p className="text-secondary text-sm">{selectedPhoto.caption}</p>
                </div>
              )}

              {/* Comments */}
              <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-0">
                {photoComments.length > 0 ? (
                  photoComments.map((comment) => (
                    <div key={comment.id} className="flex items-start gap-2 group">
                      <div className="w-7 h-7 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0">
                        <span className="text-xs font-bold text-accent">
                          {comment.user?.username?.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-primary">{comment.user?.username}</span>
                          <span className="text-xs text-muted">{formatTimestamp(comment.created_at)}</span>
                        </div>
                        <p className="text-secondary text-sm">{comment.text}</p>
                      </div>
                      <button
                        onClick={() => deletePhotoComment(comment.id)}
                        className="p-1 text-muted hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0"
                        title="Delete comment"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted text-center py-4">No comments yet</p>
                )}
              </div>

              {/* Comment input */}
              <div className="px-4 py-3 border-t border-theme">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newPhotoComment}
                    onChange={(e) => setNewPhotoComment(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        submitPhotoComment();
                      }
                    }}
                    placeholder="Add a comment..."
                    className="flex-1 px-3 py-2 bg-tertiary text-primary rounded-lg border border-theme focus:outline-none focus:ring-2 focus:ring-accent placeholder:text-muted text-sm"
                  />
                  <button
                    onClick={submitPhotoComment}
                    disabled={!newPhotoComment.trim()}
                    className="px-4 py-2 bg-accent text-white rounded-lg hover:opacity-90 transition-colors disabled:opacity-50 text-sm"
                  >
                    Post
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Video Playback Modal */}
        {selectedVideo && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setSelectedVideo(null)}>
            <div className="bg-secondary rounded-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
              {/* Modal header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-theme">
                <h3 className="font-medium text-primary truncate mr-2">
                  {selectedVideo.title || selectedVideo.original_filename || 'Video'}
                </h3>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {isOwner && (
                    <button
                      onClick={() => deleteVideo(selectedVideo.id)}
                      className="p-1 text-muted hover:text-red-400 transition-colors"
                      title="Delete video"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                  <button onClick={() => setSelectedVideo(null)} className="p-1 text-muted hover:text-primary transition-colors">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Video player */}
              <div className="flex-shrink-0 bg-black">
                <video
                  src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api'}${selectedVideo.url}`}
                  controls
                  autoPlay
                  className="w-full max-h-[60vh]"
                />
              </div>

              {/* Metadata */}
              <div className="px-4 py-3 space-y-1">
                {selectedVideo.description && (
                  <p className="text-secondary text-sm">{selectedVideo.description}</p>
                )}
                <div className="flex items-center gap-3 text-xs text-muted">
                  <span>{formatTimestamp(selectedVideo.created_at)}</span>
                  {selectedVideo.duration && (
                    <span>{formatVideoDuration(selectedVideo.duration)}</span>
                  )}
                  {selectedVideo.file_size && (
                    <span>{(selectedVideo.file_size / (1024 * 1024)).toFixed(1)} MB</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      </div>
    </ProtectedRoute>
  );
}
