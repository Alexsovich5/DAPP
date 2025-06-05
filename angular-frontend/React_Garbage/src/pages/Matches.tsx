import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Avatar,
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  CircularProgress,
  Container,
  Divider,
  Grid,
  IconButton,
  List,
  ListItem,
  ListItemAvatar,
  ListItemButton,
  ListItemText,
  Paper,
  Tab,
  Tabs,
  Typography,
  Alert,
  Stack
} from '@mui/material';
import {
  Message as MessageIcon,
  Restaurant as RestaurantIcon,
  Fastfood as FastfoodIcon,
  LocationOn as LocationIcon,
  ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';
import Navigation from '../components/navigation/Navigation';
import { useAuth } from '../context/AuthContext';

interface Match {
  _id: string;
  userId: string;
  firstName: string;
  lastName: string;
  profilePicture?: string;
  bio?: string;
  lastMessage?: {
    text: string;
    timestamp: string;
    isRead: boolean;
  };
  matchedAt: string;
  restaurantSuggestions?: Array<{
    id: string;
    name: string;
    cuisine: string;
    rating: number;
    price: string;
    imageUrl: string;
    location: string;
  }>;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`matches-tabpanel-${index}`}
      aria-labelledby={`matches-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `matches-tab-${index}`,
    'aria-controls': `matches-tabpanel-${index}`,
  };
}

const Matches: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);

  useEffect(() => {
    fetchMatches();
  }, []);

  const fetchMatches = async () => {
    setLoading(true);
    setError(null);

    try {
      // In a real app, this would fetch from your backend API
      // For demo purposes, we'll create some mock data
      const mockAPI = new Promise<Match[]>((resolve) => {
        setTimeout(() => {
          resolve([
            {
              _id: 'm1',
              userId: 'u1',
              firstName: 'Emma',
              lastName: 'Wilson',
              profilePicture: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=987&q=80',
              bio: 'Foodie and travel enthusiast. Love discovering new cuisines.',
              lastMessage: {
                text: 'I know a great Italian place downtown!',
                timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 mins ago
                isRead: false,
              },
              matchedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(), // 2 days ago
              restaurantSuggestions: [
                {
                  id: 'r1',
                  name: 'Bella Italia',
                  cuisine: 'Italian',
                  rating: 4.7,
                  price: '$$',
                  imageUrl: 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1770&q=80',
                  location: '123 Main St'
                },
                {
                  id: 'r2',
                  name: 'Sakura Sushi',
                  cuisine: 'Japanese',
                  rating: 4.5,
                  price: '$$$',
                  imageUrl: 'https://images.unsplash.com/photo-1579871494447-9811cf80d66c?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1770&q=80',
                  location: '456 Oak Ave'
                }
              ]
            },
            {
              _id: 'm2',
              userId: 'u2',
              firstName: 'Michael',
              lastName: 'Brown',
              profilePicture: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=987&q=80',
              bio: 'Chef at a local bistro. Love creating new recipes.',
              lastMessage: {
                text: 'Looking forward to our dinner date on Friday!',
                timestamp: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString(), // 3 hours ago
                isRead: true,
              },
              matchedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(), // 5 days ago
              restaurantSuggestions: [
                {
                  id: 'r3',
                  name: 'The Green Leaf',
                  cuisine: 'Vegetarian',
                  rating: 4.8,
                  price: '$$',
                  imageUrl: 'https://images.unsplash.com/photo-1540914124281-342587941389?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1974&q=80',
                  location: '789 Maple Dr'
                }
              ]
            },
            {
              _id: 'm3',
              userId: 'u3',
              firstName: 'Sophia',
              lastName: 'Garcia',
              profilePicture: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80',
              bio: 'Food blogger with a passion for pastries and coffee.',
              lastMessage: {
                text: 'Have you tried that new bakery yet?',
                timestamp: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(), // 12 hours ago
                isRead: true,
              },
              matchedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 1).toISOString(), // 1 day ago
              restaurantSuggestions: [
                {
                  id: 'r4',
                  name: 'Sweet Delights Bakery',
                  cuisine: 'Bakery & Cafe',
                  rating: 4.9,
                  price: '$',
                  imageUrl: 'https://images.unsplash.com/photo-1517433367423-c7e5b0f35086?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1780&q=80',
                  location: '321 Pine St'
                }
              ]
            }
          ]);
        }, 1500);
      });

      const response = await mockAPI;
      setMatches(response);
    } catch (err) {
      console.error('Error fetching matches:', err);
      setError('Failed to load matches. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleChatClick = (userId: string) => {
    navigate(`/chat/${userId}`);
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
      return 'Yesterday';
    }
    
    // Within a week
    const oneWeek = 7 * 24 * 60 * 60 * 1000;
    if ((now.getTime() - date.getTime()) < oneWeek) {
      return date.toLocaleDateString([], { weekday: 'short' });
    }
    
    // Older
    return date.toLocaleDateString();
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
        <Paper elevation={2} sx={{ borderRadius: 2 }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs 
              value={tabValue} 
              onChange={handleTabChange} 
              aria-label="match tabs"
              variant="fullWidth"
            >
              <Tab label="Messages" {...a11yProps(0)} />
              <Tab label="Restaurant Suggestions" {...a11yProps(1)} />
            </Tabs>
          </Box>
          
          {error && (
            <Alert severity="error" sx={{ m: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          
          {matches.length === 0 && !loading && !error && (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <RestaurantIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                No Matches Yet
              </Typography>
              <Typography variant="body1" paragraph>
                Start discovering potential matches to connect with fellow food lovers!
              </Typography>
              <Button 
                variant="contained" 
                onClick={() => navigate('/discover')}
                startIcon={<RestaurantIcon />}
              >
                Discover
              </Button>
            </Box>
          )}

          {/* Messages Tab */}
          <TabPanel value={tabValue} index={0}>
            <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
              {matches.map((match, index) => (
                <React.Fragment key={match._id}>
                  <ListItem
                    alignItems="flex-start"
                    secondaryAction={
                      <IconButton 
                        edge="end" 
                        aria-label="message" 
                        onClick={() => handleChatClick(match.userId)}
                      >
                        <MessageIcon />
                      </IconButton>
                    }
                    disablePadding
                  >
                    <ListItemButton onClick={() => handleChatClick(match.userId)}>
                      <ListItemAvatar>
                        <Avatar 
                          alt={match.firstName} 
                          src={match.profilePicture}
                          sx={{ width: 56, height: 56, mr: 2 }}
                        />
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Typography 
                              variant="subtitle1"
                              sx={{ fontWeight: match.lastMessage?.isRead ? 'normal' : 'bold' }}
                            >
                              {match.firstName} {match.lastName}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {match.lastMessage ? formatTime(match.lastMessage.timestamp) : 'New match'}
                            </Typography>
                          </Box>
                        }
                        secondary={
                          <Typography
                            variant="body2"
                            color="text.primary"
                            sx={{ 
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              display: '-webkit-box',
                              WebkitLineClamp: 1,
                              WebkitBoxOrient: 'vertical',
                              fontWeight: match.lastMessage?.isRead ? 'normal' : 'bold'
                            }}
                          >
                            {match.lastMessage?.text || 'Say hello!'}
                          </Typography>
                        }
                      />
                    </ListItemButton>
                  </ListItem>
                  {index < matches.length - 1 && <Divider variant="inset" component="li" />}
                </React.Fragment>
              ))}
            </List>
          </TabPanel>

          {/* Restaurant Suggestions Tab */}
          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={3}>
              {matches.flatMap(match => 
                match.restaurantSuggestions?.map(restaurant => (
                  <Grid item={true} xs={12} md={6} key={restaurant.id}>
                    <Card sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                      <CardActionArea>
                        <Box sx={{ position: 'relative', height: 200 }}>
                          <Box
                            component="img"
                            sx={{
                              width: '100%',
                              height: '100%',
                              objectFit: 'cover',
                            }}
                            src={restaurant.imageUrl}
                            alt={restaurant.name}
                          />
                          <Box
                            sx={{
                              position: 'absolute',
                              bottom: 0,
                              left: 0,
                              right: 0,
                              bgcolor: 'rgba(0, 0, 0, 0.5)',
                              color: 'white',
                              p: 1,
                            }}
                          >
                            <Typography variant="subtitle1">{restaurant.name}</Typography>
                            <Stack direction="row" spacing={1} alignItems="center">
                              <FastfoodIcon fontSize="small" />
                              <Typography variant="body2">{restaurant.cuisine}</Typography>
                              <Typography variant="body2">•</Typography>
                              <Typography variant="body2">{restaurant.price}</Typography>
                              <Typography variant="body2">•</Typography>
                              <Typography variant="body2">{restaurant.rating} ★</Typography>
                            </Stack>
                          </Box>
                        </Box>
                        <CardContent>
                          <Stack direction="row" spacing={1} alignItems="center">
                            <LocationIcon fontSize="small" />
                            <Typography variant="body2" color="text.secondary">
                              {restaurant.location}
                            </Typography>
                          </Stack>
                          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Avatar
                                alt={match.firstName}
                                src={match.profilePicture}
                                sx={{ width: 32, height: 32 }}
                              />
                              <Typography variant="body2">
                                Suggested by {match.firstName}
                              </Typography>
                            </Stack>
                            <Button 
                              endIcon={<ArrowForwardIcon />}
                              size="small"
                              onClick={() => handleChatClick(match.userId)}
                            >
                              Discuss
                            </Button>
                          </Box>
                        </CardContent>
                      </CardActionArea>
                    </Card>
                  </Grid>
                ))
              )}
            </Grid>
          </TabPanel>
        </Paper>
      </Container>
    </>
  );
};

export default Matches;