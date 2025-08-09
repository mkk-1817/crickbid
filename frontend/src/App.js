import React, { useState, useEffect } from 'react';
import './App.css';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Progress } from './components/ui/progress';
import { Separator } from './components/ui/separator';
import { Avatar, AvatarFallback } from './components/ui/avatar';
import { Crown, Users, Timer, Trophy, Gavel, Star } from 'lucide-react';
import axios from 'axios';
import io from 'socket.io-client';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentView, setCurrentView] = useState('home'); // home, create, join, auction
  const [roomCode, setRoomCode] = useState('');
  const [teamName, setTeamName] = useState('');
  const [socket, setSocket] = useState(null);
  const [gameState, setGameState] = useState({
    teams: [],
    currentPlayer: null,
    currentBid: 0,
    currentBidder: '',
    timeLeft: 30,
    myTeam: null,
    auctionStarted: false
  });

  // Connect to socket when joining a room
  useEffect(() => {
    if (currentView === 'auction' && roomCode) {
      const newSocket = io(BACKEND_URL);
      setSocket(newSocket);

      newSocket.on('connect', () => {
        console.log('Connected to server');
        newSocket.emit('join_room', { room_code: roomCode, team_name: teamName });
      });

      newSocket.on('team_joined', (data) => {
        setGameState(prev => ({
          ...prev,
          teams: [...prev.teams, data.team]
        }));
      });

      newSocket.on('auction_started', (data) => {
        setGameState(prev => ({
          ...prev,
          currentPlayer: data.current_player,
          currentBid: data.current_bid,
          auctionStarted: true,
          timeLeft: 30
        }));
      });

      newSocket.on('new_bid', (data) => {
        setGameState(prev => ({
          ...prev,
          currentBid: data.bid_amount,
          currentBidder: data.bidder_team,
          timeLeft: 30
        }));
      });

      newSocket.on('error', (data) => {
        alert(data.message);
      });

      return () => {
        newSocket.disconnect();
      };
    }
  }, [currentView, roomCode, teamName]);

  // Timer countdown
  useEffect(() => {
    if (gameState.auctionStarted && gameState.timeLeft > 0) {
      const timer = setTimeout(() => {
        setGameState(prev => ({
          ...prev,
          timeLeft: prev.timeLeft - 1
        }));
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [gameState.timeLeft, gameState.auctionStarted]);

  const createRoom = async () => {
    try {
      const response = await axios.post(`${API}/room/create`);
      setRoomCode(response.data.room_code);
      setCurrentView('create');
    } catch (error) {
      console.error('Error creating room:', error);
    }
  };

  const joinRoom = () => {
    if (roomCode && teamName) {
      setCurrentView('auction');
    }
  };

  const startAuction = async () => {
    try {
      await axios.post(`${API}/room/${roomCode}/start`);
    } catch (error) {
      console.error('Error starting auction:', error);
    }
  };

  const placeBid = () => {
    if (socket) {
      const bidAmount = gameState.currentBid + 25; // Increment by 25 lakhs
      socket.emit('place_bid', { room_code: roomCode, bid_amount: bidAmount });
    }
  };

  const renderHome = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0">
        <div className="absolute top-20 left-20 w-72 h-72 bg-yellow-400 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
        <div className="absolute top-40 right-20 w-72 h-72 bg-pink-400 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-40 w-72 h-72 bg-blue-400 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-4000"></div>
      </div>
      
      <div className="relative z-10 container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <div className="flex justify-center mb-8">
            <div className="relative">
              <Crown className="w-20 h-20 text-yellow-400 animate-bounce" />
              <div className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full animate-ping"></div>
            </div>
          </div>
          <h1 className="text-6xl font-bold text-white mb-6 bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 bg-clip-text text-transparent">
            Cricket Auction Arena
          </h1>
          <p className="text-xl text-blue-200 mb-8 max-w-2xl mx-auto leading-relaxed">
            Build your ultimate cricket team in the most exciting auction experience. 
            Compete with up to 8 players and manage your 80 crore budget wisely!
          </p>
          
          {/* Feature highlights */}
          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto mb-12">
            <div className="text-center p-6 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20">
              <Users className="w-12 h-12 text-blue-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">Up to 8 Teams</h3>
              <p className="text-blue-200 text-sm">Compete with friends in real-time multiplayer auction</p>
            </div>
            <div className="text-center p-6 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20">
              <Trophy className="w-12 h-12 text-yellow-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">200+ Players</h3>
              <p className="text-blue-200 text-sm">Choose from international cricket stars</p>
            </div>
            <div className="text-center p-6 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20">
              <Timer className="w-12 h-12 text-green-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">30s Timer</h3>
              <p className="text-blue-200 text-sm">Fast-paced bidding with 30-second rounds</p>
            </div>
          </div>
        </div>

        <div className="max-w-md mx-auto space-y-6">
          <Card className="bg-white/10 backdrop-blur-md border-white/20 shadow-2xl">
            <CardContent className="p-8">
              <Button 
                onClick={createRoom}
                className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white border-0 rounded-xl shadow-lg transform hover:scale-105 transition-all duration-200"
              >
                <Crown className="w-6 h-6 mr-3" />
                Create New Auction
              </Button>
            </CardContent>
          </Card>

          <div className="text-center">
            <span className="text-blue-200 font-medium">OR</span>
          </div>

          <Card className="bg-white/10 backdrop-blur-md border-white/20 shadow-2xl">
            <CardContent className="p-8 space-y-4">
              <Input
                placeholder="Enter 6-digit room code"
                value={roomCode}
                onChange={(e) => setRoomCode(e.target.value)}
                className="h-12 text-center text-lg font-mono bg-white/20 border-white/30 text-white placeholder-blue-200"
                maxLength={6}
              />
              <Input
                placeholder="Enter your team name"
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                className="h-12 text-center text-lg bg-white/20 border-white/30 text-white placeholder-blue-200"
              />
              <Button 
                onClick={joinRoom}
                disabled={!roomCode || !teamName}
                className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white border-0 rounded-xl shadow-lg transform hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:transform-none"
              >
                <Users className="w-6 h-6 mr-3" />
                Join Auction
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );

  const renderCreate = () => (
    <div className="min-h-screen bg-gradient-to-br from-green-900 via-emerald-900 to-teal-900 p-8">
      <div className="max-w-2xl mx-auto">
        <Card className="bg-white/10 backdrop-blur-md border-white/20 shadow-2xl">
          <CardHeader className="text-center pb-8">
            <Crown className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
            <CardTitle className="text-3xl font-bold text-white">Auction Created!</CardTitle>
            <p className="text-green-200 mt-2">Share this code with other players</p>
          </CardHeader>
          <CardContent className="space-y-8">
            <div className="text-center">
              <div className="bg-white/20 rounded-2xl p-8 mb-6">
                <p className="text-green-200 mb-2">Room Code</p>
                <p className="text-5xl font-mono font-bold text-white tracking-wider">{roomCode}</p>
              </div>
              <p className="text-green-200 mb-6">Waiting for teams to join...</p>
              <div className="space-y-4">
                <Input
                  placeholder="Enter your team name"
                  value={teamName}
                  onChange={(e) => setTeamName(e.target.value)}
                  className="h-12 text-center text-lg bg-white/20 border-white/30 text-white placeholder-green-200"
                />
                <Button 
                  onClick={joinRoom}
                  disabled={!teamName}
                  className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-yellow-500 to-orange-600 hover:from-yellow-600 hover:to-orange-700 text-white border-0 rounded-xl"
                >
                  Join as Host
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderAuction = () => (
    <div className="min-h-screen bg-gradient-to-br from-orange-900 via-red-900 to-pink-900">
      {/* Header */}
      <div className="bg-black/30 backdrop-blur-md border-b border-white/10 p-4">
        <div className="container mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <Gavel className="w-8 h-8 text-yellow-400" />
            <span className="text-2xl font-bold text-white">Cricket Auction</span>
            <Badge variant="secondary" className="bg-yellow-400/20 text-yellow-400 border-yellow-400/30">
              Room: {roomCode}
            </Badge>
          </div>
          <div className="flex items-center space-x-4">
            <Badge variant="secondary" className="bg-blue-400/20 text-blue-200 border-blue-400/30">
              <Users className="w-4 h-4 mr-2" />
              {gameState.teams.length} Teams
            </Badge>
          </div>
        </div>
      </div>

      <div className="container mx-auto p-6">
        {!gameState.auctionStarted ? (
          <div className="text-center py-20">
            <Card className="max-w-2xl mx-auto bg-white/10 backdrop-blur-md border-white/20">
              <CardContent className="p-12">
                <Trophy className="w-20 h-20 text-yellow-400 mx-auto mb-6" />
                <h2 className="text-3xl font-bold text-white mb-4">Ready to Start?</h2>
                <p className="text-blue-200 mb-8">All teams have joined. Let's begin the auction!</p>
                <Button 
                  onClick={startAuction}
                  className="h-16 px-12 text-xl font-semibold bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white border-0 rounded-xl"
                >
                  <Crown className="w-8 h-8 mr-4" />
                  Start Auction
                </Button>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Current Player Card */}
            <div className="lg:col-span-2">
              <Card className="bg-white/10 backdrop-blur-md border-white/20 shadow-2xl">
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <CardTitle className="text-2xl font-bold text-white">Current Player</CardTitle>
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center bg-red-500/20 rounded-full px-4 py-2">
                        <Timer className="w-5 h-5 text-red-400 mr-2" />
                        <span className="text-red-400 font-bold text-lg">{gameState.timeLeft}s</span>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {gameState.currentPlayer && (
                    <div className="space-y-6">
                      <div className="text-center">
                        <Avatar className="w-32 h-32 mx-auto mb-4 bg-gradient-to-br from-blue-400 to-purple-600">
                          <AvatarFallback className="text-4xl font-bold text-white">
                            {gameState.currentPlayer.name.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <h3 className="text-3xl font-bold text-white mb-2">{gameState.currentPlayer.name}</h3>
                        <div className="flex justify-center items-center space-x-4 mb-4">
                          <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                            {gameState.currentPlayer.role}
                          </Badge>
                          <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                            {gameState.currentPlayer.country}
                          </Badge>
                          <div className="flex items-center">
                            {[...Array(gameState.currentPlayer.rating)].map((_, i) => (
                              <Star key={i} className="w-4 h-4 text-yellow-400 fill-current" />
                            ))}
                          </div>
                        </div>
                        <div className="bg-white/10 rounded-xl p-6">
                          <p className="text-blue-200 mb-2">Current Bid</p>
                          <p className="text-4xl font-bold text-white">₹{gameState.currentBid} L</p>
                          {gameState.currentBidder && (
                            <p className="text-yellow-400 mt-2">Leading: {gameState.currentBidder}</p>
                          )}
                        </div>
                      </div>
                      
                      <div className="text-center">
                        <Button 
                          onClick={placeBid}
                          className="h-16 px-12 text-xl font-semibold bg-gradient-to-r from-yellow-500 to-orange-600 hover:from-yellow-600 hover:to-orange-700 text-white border-0 rounded-xl transform hover:scale-105 transition-all duration-200"
                        >
                          <Gavel className="w-6 h-6 mr-3" />
                          Bid ₹{gameState.currentBid + 25} L
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Teams Panel */}
            <div>
              <Card className="bg-white/10 backdrop-blur-md border-white/20 shadow-2xl">
                <CardHeader>
                  <CardTitle className="text-xl font-bold text-white flex items-center">
                    <Users className="w-6 h-6 mr-2" />
                    Teams ({gameState.teams.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {gameState.teams.map((team, index) => (
                    <div key={team.id} className="bg-white/10 rounded-xl p-4">
                      <div className="flex justify-between items-center mb-3">
                        <h4 className="font-bold text-white">{team.name}</h4>
                        <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                          {team.players?.length || 0}/15
                        </Badge>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-blue-200">Budget</span>
                          <span className="text-white font-medium">₹{team.budget} L</span>
                        </div>
                        <Progress 
                          value={(team.budget / 8000) * 100} 
                          className="h-2 bg-white/20"
                        />
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="App">
      {currentView === 'home' && renderHome()}
      {currentView === 'create' && renderCreate()}
      {currentView === 'auction' && renderAuction()}
    </div>
  );
}

export default App;