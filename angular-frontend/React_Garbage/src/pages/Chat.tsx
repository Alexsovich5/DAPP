import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Avatar,
  Box,
  Button,
  CircularProgress,
  Container,
  Divider,
  IconButton,
  InputAdornment,
  Paper,
  TextField,
  Typography,
  Alert,
  Stack
} from '@mui/material';
import {
  Send as SendIcon,
  ArrowBack as ArrowBackIcon,
  AttachFile as AttachFileIcon,
  Restaurant as RestaurantIcon,
  InsertEmoticon as EmojiIcon
} from '@mui/icons-material';
import Navigation from '../components/navigation/Navigation';
import { useAuth } from '../context/AuthContext';

interface Message {
  id: string;
  senderId: string;
  content: string;
  timestamp: string;
  isRead: boolean;
}

interface ChatUser {
  _id: string;
  firstName: string;
  lastName: string;
  profilePicture?: string;
  lastActive?: string;
}

const Chat: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatPartner, setChatPartner] = useState<ChatUser | null>(null);
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (userId) {
      fetchChatData();
    } else {
      setError('Invalid chat. Please go back to matches.');
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchChatData = async () => {
    setLoading(true);
    setError(null);

    try {
      // In a real app, this would fetch from your backend API
      // For demo purposes, we'll create some mock data

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Mock user data
      const mockUsers: Record<string, ChatUser> = {
        'u1': {
          _id: 'u1',
          firstName: 'Emma',
          lastName: 'Wilson',
          profilePicture: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=987&q=80',
          lastActive: new Date(Date.now() - 1000 * 60 * 15).toISOString() // 15 mins ago
        },
        'u2': {
          _id: 'u2',
          firstName: 'Michael',
          lastName: 'Brown',
          profilePicture: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=987&q=80',
          lastActive: new Date(Date.now() - 1000 * 60 * 5).toISOString() // 5 mins ago
        },
        'u3': {
          _id: 'u3',
          firstName: 'Sophia',
          lastName: 'Garcia',
          profilePicture: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80',
          lastActive: new Date().toISOString() // Just now
        }
      };

      const mockMessagesByUser: Record<string, Message[]> = {
        'u1': [
          {
            id: 'm1',
            senderId: 'u1',
            content: 'Hey there! I noticed you like Italian food. Have you been to that new place downtown?',
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
            isRead: true
          },
          {
            id: 'm2',
            senderId: 'currentUser',
            content: 'Hi Emma! I haven\'t been yet, but it\'s on my list. I heard they have amazing pasta!',
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 23).toISOString(), // 23 hours ago
            isRead: true
          },
          {
            id: 'm3',
            senderId: 'u1',
            content: 'They do! Their carbonara is to die for. Would you like to check it out together sometime?',
            timestamp: new Date(Date.now() - 1000 * 60 * 35).toISOString(), // 35 mins ago
            isRead: true
          },
          {
            id: 'm4',
            senderId: 'currentUser',
            content: 'That sounds great! When were you thinking?',
            timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 mins ago
            isRead: true
          },
          {
            id: 'm5',
            senderId: 'u1',
            content: 'I know a great Italian place downtown!',
            timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(), // 15 mins ago
            isRead: false
          }
        ],
        'u2': [
          {
            id: 'm1',
            senderId: 'currentUser',
            content: 'Hey Michael, I really enjoyed your profile. I see you\'re a chef!',
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(), // 5 hours ago
            isRead: true
          },
          {
            id: 'm2',
            senderId: 'u2',
            content: 'Hey! Yes, I work at a bistro downtown. I specialize in French cuisine.',
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString(), // 4 hours ago
            isRead: true
          },
          {
            id: 'm3',
            senderId: 'currentUser',
            content: 'That\'s amazing! I love French food. What\'s your signature dish?',
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 3.5).toISOString(), // 3.5 hours ago
            isRead: true
          },
          {
            id: 'm4',
            senderId: 'u2',
            content: 'Looking forward to our dinner date on Friday!',
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString(), // 3 hours ago
            isRead: true
          }
        ],
        'u3': [
          {
            id: 'm1',
            senderId: 'u3',
            content: 'I saw that we both love baking! What\'s your favorite thing to bake?',
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 14).toISOString(), // 14 hours ago
            isRead: true
          },
          {
            id: 'm2',
            senderId: 'currentUser',
            content: 'I love making sourdough bread and pastries! How about you?',
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 13).toISOString(), // 13 hours ago
            isRead: true
          },
          {
            id: 'm3',
            senderId: 'u3',
            content: 'That\'s awesome! I\'m more into cakes and cookies. Have you tried that new bakery on 5th Street?',
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 12.5).toISOString(), // 12.5 hours ago
            isRead: true
          },
          {
            id: 'm4',
            senderId: 'currentUser',
            content: 'Not yet! Is it good?',
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 12.4).toISOString(), // 12.4 hours ago
            isRead: true
          },
          {
            id: 'm5',
            senderId: 'u3',
            content: 'Have you tried that new bakery yet?',
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(), // 12 hours ago
            isRead: true
          }
        ]
      };

      if (userId && mockUsers[userId]) {
        setChatPartner(mockUsers[userId]);
        
        // Get messages for this user
        const userMessages = mockMessagesByUser[userId] || [];
        setMessages(userMessages);
      } else {
        setError('User not found');
      }
    } catch (err) {
      console.error('Error fetching chat data:', err);
      setError('Failed to load chat. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || sending) return;

    setSending(true);
    
    try {
      // In a real app, you would send this to your API
      const newMsg: Message = {
        id: `new-${Date.now()}`,
        senderId: 'currentUser',
        content: newMessage.trim(),
        timestamp: new Date().toISOString(),
        isRead: false,
      };
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setMessages(prev => [...prev, newMsg]);
      setNewMessage('');
    } catch (err) {
      setError('Failed to send message. Please try again.');
    } finally {
      setSending(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    
    // Today
    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // Yesterday
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    if (date.toDateString() === yesterday.toDateString()) {
      return `Yesterday ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }
    
    // Older
    return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  };

  if (loading) {
    return (
      <>
        <Navigation />
        <Container sx={{ mt: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', height: '70vh' }}>
          <CircularProgress />
        </Container>
      </>
    );
  }

  return (
    <>
      <Navigation />
      <Container maxWidth="md" sx={{ mt: 4, mb: 10 }}>
        <Paper elevation={3} sx={{ borderRadius: 2, overflow: 'hidden', height: 'calc(100vh - 200px)' }}>
          {/* Chat Header */}
          <Box
            sx={{
              p: 2,
              bgcolor: 'primary.main',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              position: 'sticky',
              top: 0,
              zIndex: 1,
            }}
          >
            <Stack direction="row" spacing={2} alignItems="center">
              <IconButton color="inherit" onClick={() => navigate('/matches')}>
                <ArrowBackIcon />
              </IconButton>
              <Avatar
                alt={chatPartner?.firstName}
                src={chatPartner?.profilePicture}
                sx={{ width: 48, height: 48 }}
              />
              <Box>
                <Typography variant="subtitle1">
                  {chatPartner?.firstName} {chatPartner?.lastName}
                </Typography>
                <Typography variant="caption">
                  {chatPartner?.lastActive ? 'Online' : 'Offline'}
                </Typography>
              </Box>
            </Stack>
            <IconButton
              color="inherit"
              onClick={() => navigate('/preferences')}
              title="Suggest a restaurant"
            >
              <RestaurantIcon />
            </IconButton>
          </Box>
          
          {/* Error Alert */}
          {error && (
            <Alert severity="error" sx={{ m: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          
          {/* Chat Messages */}
          <Box
            sx={{
              p: 2,
              height: 'calc(100% - 136px)',
              overflowY: 'auto',
              bgcolor: 'grey.50',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {messages.length === 0 ? (
              <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography variant="body1" color="text.secondary">
                  No messages yet. Say hello!
                </Typography>
              </Box>
            ) : (
              messages.map((message, index) => {
                const isCurrentUser = message.senderId === 'currentUser';
                const showDate = index === 0 || 
                  new Date(message.timestamp).toDateString() !== 
                  new Date(messages[index - 1].timestamp).toDateString();
                
                return (
                  <React.Fragment key={message.id}>
                    {showDate && (
                      <Divider sx={{ my: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(message.timestamp).toLocaleDateString()}
                        </Typography>
                      </Divider>
                    )}
                    <Box
                      sx={{
                        maxWidth: '75%',
                        alignSelf: isCurrentUser ? 'flex-end' : 'flex-start',
                        mb: 1.5,
                      }}
                    >
                      <Paper
                        elevation={1}
                        sx={{
                          p: 1.5,
                          bgcolor: isCurrentUser ? 'primary.light' : 'background.paper',
                          color: isCurrentUser ? 'white' : 'text.primary',
                          borderRadius: 2,
                          borderTopRightRadius: isCurrentUser ? 0 : 2,
                          borderTopLeftRadius: isCurrentUser ? 2 : 0,
                        }}
                      >
                        <Typography variant="body1">{message.content}</Typography>
                        <Typography 
                          variant="caption" 
                          sx={{ 
                            display: 'block', 
                            textAlign: 'right', 
                            mt: 0.5,
                            opacity: 0.8
                          }}
                        >
                          {formatTime(message.timestamp)}
                        </Typography>
                      </Paper>
                    </Box>
                  </React.Fragment>
                );
              })
            )}
            <div ref={messagesEndRef} />
          </Box>
          
          {/* Message Input */}
          <Box
            sx={{
              p: 2,
              bgcolor: 'background.paper',
              borderTop: 1,
              borderColor: 'divider',
              position: 'sticky',
              bottom: 0,
            }}
          >
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
            >
              <TextField
                fullWidth
                placeholder="Type a message..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                disabled={sending}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <IconButton size="small">
                        <EmojiIcon />
                      </IconButton>
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton size="small">
                        <AttachFileIcon />
                      </IconButton>
                      <IconButton 
                        type="submit" 
                        color="primary"
                        disabled={!newMessage.trim() || sending}
                      >
                        {sending ? <CircularProgress size={24} /> : <SendIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                  sx: { borderRadius: 4, px: 1 }
                }}
                variant="outlined"
              />
            </form>
          </Box>
        </Paper>
      </Container>
    </>
  );
};

export default Chat;