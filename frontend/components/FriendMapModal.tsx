'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { GoogleMap, useJsApiLoader, Marker, InfoWindow, DirectionsRenderer } from '@react-google-maps/api';
import { Socket } from 'socket.io-client';
import { api } from '@/lib/api';

interface FriendLocation {
  user_id: number;
  username: string;
  latitude: number;
  longitude: number;
  updated_at?: string;
}

interface FriendMapModalProps {
  isOpen: boolean;
  onClose: () => void;
  showId: number;
  socket: Socket | null;
  userLocation: { lat: number; lng: number } | null;
  venueLocation?: { lat: number; lng: number } | null;
}

const mapContainerStyle = {
  width: '100%',
  height: '100%',
};

export default function FriendMapModal({
  isOpen,
  onClose,
  showId,
  socket,
  userLocation,
  venueLocation,
}: FriendMapModalProps) {
  const [friends, setFriends] = useState<FriendLocation[]>([]);
  const [selectedFriend, setSelectedFriend] = useState<FriendLocation | null>(null);
  const [directions, setDirections] = useState<google.maps.DirectionsResult | null>(null);
  const [walkingInfo, setWalkingInfo] = useState<{ distance: string; duration: string } | null>(null);
  const mapRef = useRef<google.maps.Map | null>(null);

  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || '',
  });

  // Fetch friend locations via REST when modal opens
  useEffect(() => {
    if (!isOpen) return;

    const fetchFriends = async () => {
      try {
        const response = await api.get(`/shows/${showId}/presence`);
        const users = response.data.users || [];
        const friendsWithLocation = users
          .filter((u: { is_friend: boolean; latitude?: number }) => u.is_friend && u.latitude != null)
          .map((u: { id: number; username: string; latitude: number; longitude: number; last_seen?: string }) => ({
            user_id: u.id,
            username: u.username,
            latitude: u.latitude,
            longitude: u.longitude,
            updated_at: u.last_seen,
          }));
        setFriends(friendsWithLocation);
      } catch (error) {
        console.error('Failed to fetch friend locations:', error);
      }
    };

    fetchFriends();
  }, [isOpen, showId]);

  // Listen for real-time location updates
  useEffect(() => {
    if (!isOpen || !socket) return;

    const handleLocationUpdate = (data: FriendLocation) => {
      setFriends(prev => {
        const idx = prev.findIndex(f => f.user_id === data.user_id);
        if (idx >= 0) {
          const updated = [...prev];
          updated[idx] = data;
          return updated;
        }
        return [...prev, data];
      });
    };

    const handleFriendsLocations = (data: { friends: FriendLocation[] }) => {
      setFriends(data.friends);
    };

    const handleLocationStopped = (data: { user_id: number }) => {
      setFriends(prev => prev.filter(f => f.user_id !== data.user_id));
      if (selectedFriend?.user_id === data.user_id) {
        setSelectedFriend(null);
        setDirections(null);
        setWalkingInfo(null);
      }
    };

    socket.on('location_update', handleLocationUpdate);
    socket.on('friends_locations', handleFriendsLocations);
    socket.on('location_stopped', handleLocationStopped);

    return () => {
      socket.off('location_update', handleLocationUpdate);
      socket.off('friends_locations', handleFriendsLocations);
      socket.off('location_stopped', handleLocationStopped);
    };
  }, [isOpen, socket, selectedFriend]);

  // Fetch walking directions when a friend is selected
  const fetchDirections = useCallback((friend: FriendLocation) => {
    if (!userLocation || !isLoaded) return;

    const directionsService = new google.maps.DirectionsService();
    directionsService.route(
      {
        origin: userLocation,
        destination: { lat: friend.latitude, lng: friend.longitude },
        travelMode: google.maps.TravelMode.WALKING,
      },
      (result, status) => {
        if (status === google.maps.DirectionsStatus.OK && result) {
          setDirections(result);
          const leg = result.routes[0]?.legs[0];
          if (leg) {
            setWalkingInfo({
              distance: leg.distance?.text || '',
              duration: leg.duration?.text || '',
            });
          }
        } else {
          setDirections(null);
          setWalkingInfo(null);
        }
      }
    );
  }, [userLocation, isLoaded]);

  const handleSelectFriend = (friend: FriendLocation) => {
    setSelectedFriend(friend);
    fetchDirections(friend);
    if (mapRef.current) {
      mapRef.current.panTo({ lat: friend.latitude, lng: friend.longitude });
    }
  };

  const handleMarkerClick = (friend: FriendLocation) => {
    console.warn('[FriendMap] Marker clicked:', friend.username, friend.latitude, friend.longitude);
    setSelectedFriend(friend);
    fetchDirections(friend);
  };

  const onMapLoad = useCallback((map: google.maps.Map) => {
    mapRef.current = map;
  }, []);

  if (!isOpen) return null;

  const center = userLocation || venueLocation || { lat: 40.7128, lng: -74.006 };

  return (
    <div className="fixed inset-0 bg-black/80 flex flex-col z-50" onClick={onClose}>
      <div className="flex-1 flex flex-col" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-secondary border-b border-theme">
          <h2 className="text-lg font-bold text-primary">Find My Friends</h2>
          <button onClick={onClose} className="p-1 text-muted hover:text-primary transition-colors">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Map */}
        <div className="flex-1 relative">
          {isLoaded ? (
            <GoogleMap
              mapContainerStyle={mapContainerStyle}
              center={center}
              zoom={17}
              onLoad={onMapLoad}
              options={{
                disableDefaultUI: false,
                zoomControl: true,
                streetViewControl: false,
                mapTypeControl: false,
                fullscreenControl: false,
              }}
            >
              {/* User marker (blue dot) */}
              {userLocation && (
                <Marker
                  position={userLocation}
                  icon={{
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 10,
                    fillColor: '#4285F4',
                    fillOpacity: 1,
                    strokeColor: '#ffffff',
                    strokeWeight: 3,
                  }}
                  title="You"
                  zIndex={1000}
                />
              )}

              {/* Friend markers */}
              {friends.map((friend) => (
                <Marker
                  key={friend.user_id}
                  position={{ lat: friend.latitude, lng: friend.longitude }}
                  label={{
                    text: friend.username.charAt(0).toUpperCase(),
                    color: '#ffffff',
                    fontSize: '14px',
                    fontWeight: 'bold',
                    className: 'friend-marker-label',
                  }}
                  clickable={true}
                  onClick={() => handleMarkerClick(friend)}
                  icon={{
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 18,
                    fillColor: '#EA4335',
                    fillOpacity: 1,
                    strokeColor: '#ffffff',
                    strokeWeight: 2,
                    labelOrigin: new google.maps.Point(0, 0),
                  }}
                />
              ))}

              {/* InfoWindow for selected friend */}
              {selectedFriend && (
                <InfoWindow
                  position={{ lat: selectedFriend.latitude, lng: selectedFriend.longitude }}
                  onCloseClick={() => {
                    setSelectedFriend(null);
                    setDirections(null);
                    setWalkingInfo(null);
                  }}
                >
                  <div style={{ color: '#333', minWidth: '120px' }}>
                    <p style={{ fontWeight: 'bold', marginBottom: '4px' }}>{selectedFriend.username}</p>
                    {walkingInfo && (
                      <p style={{ fontSize: '13px', margin: 0 }}>
                        {walkingInfo.distance} &middot; {walkingInfo.duration} walk
                      </p>
                    )}
                  </div>
                </InfoWindow>
              )}

              {/* Walking directions */}
              {directions && (
                <DirectionsRenderer
                  directions={directions}
                  options={{
                    suppressMarkers: true,
                    polylineOptions: {
                      strokeColor: '#4285F4',
                      strokeWeight: 4,
                      strokeOpacity: 0.8,
                    },
                  }}
                />
              )}
            </GoogleMap>
          ) : (
            <div className="flex items-center justify-center h-full bg-tertiary">
              <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-accent"></div>
            </div>
          )}
        </div>

        {/* Friend list panel */}
        <div className="bg-secondary border-t border-theme max-h-48 overflow-y-auto">
          {friends.length > 0 ? (
            <div>
              <div className="px-4 py-2 border-b border-theme">
                <p className="text-xs text-muted font-medium uppercase tracking-wide">
                  {friends.length} friend{friends.length !== 1 ? 's' : ''} sharing location
                </p>
              </div>
              {friends.map((friend) => (
                <button
                  key={friend.user_id}
                  onClick={() => handleSelectFriend(friend)}
                  className={`w-full flex items-center gap-3 px-4 py-3 border-b border-theme last:border-b-0 transition-colors ${
                    selectedFriend?.user_id === friend.user_id ? 'bg-accent/10' : 'hover:bg-tertiary'
                  }`}
                >
                  <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-bold text-accent">
                      {friend.username.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1 text-left">
                    <p className="text-sm font-medium text-primary">{friend.username}</p>
                    {selectedFriend?.user_id === friend.user_id && walkingInfo && (
                      <p className="text-xs text-muted">{walkingInfo.distance} &middot; {walkingInfo.duration} walk</p>
                    )}
                  </div>
                  <svg className="w-4 h-4 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </button>
              ))}
            </div>
          ) : (
            <div className="px-4 py-6 text-center">
              <p className="text-sm text-muted">No friends sharing their location yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
