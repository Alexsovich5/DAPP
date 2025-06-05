import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  CardMedia,
  CircularProgress,
  Container,
  Divider,
  IconButton,
  Paper,
  Stack,
  Typography,
  Chip,
  Alert
} from '@mui/material';
import {
  Close as CloseIcon,
  Favorite as FavoriteIcon,
  Restaurant as RestaurantIcon,
  Cake as CakeIcon,
  LocationOn as LocationIcon
} from '@mui/icons-material';
import axios from 'axios';
import Navigation from '../components/navigation/Navigation';
import { useAuth } from '../context/AuthContext';

interface PotentialMatch {
  _id: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  gender: string;
  bio?: string;
  interests?: string[];
  profilePictures: string[];
  dietaryPreferences?: string[];
  distance?: number;
  age?: number;
}

const calculateAge = (dateOfBirth: string): number => {
  const today = new Date();
  const birthDate = new Date(dateOfBirth);
  let age = today.getFullYear() - birthDate.getFullYear();
  const m = today.getMonth() - birthDate.getMonth();
  
  if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  
  return age;
};

const Discover: React.FC = () => {
  const { user } = useAuth();
  const [potentialMatches, setPotentialMatches] = useState<PotentialMatch[]>([]);
  const [currentMatch, setCurrentMatch] = useState<PotentialMatch | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionInProgress, setActionInProgress] = useState(false);

  useEffect(() => {
    fetchPotentialMatches();
  }, []);

  const fetchPotentialMatches = async () => {
    setLoading(true);
    setError(null);

    try {
      // In a real app, this would fetch from your backend API
      // For demo purposes, we'll create some mock data
      const mockAPI = new Promise<PotentialMatch[]>((resolve) => {
        setTimeout(() => {
          resolve([
            {
              _id: '1',
              firstName: 'Jane',
              lastName: 'Doe',
              dateOfBirth: new Date('1995-05-12').toISOString(),
              gender: 'female',
              bio: 'Food enthusiast who loves trying new restaurants. Big fan of Italian cuisine and desserts.',
              interests: ['cooking', 'dining out', 'wine tasting', 'baking', 'travel'],
              profilePictures: ['https://images.unsplash.com/photo-1494790108377-be9c29b29330?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1587&q=80'],
              dietaryPreferences: ['pescatarian', 'gluten-free'],
              distance: 5,
              age: 28
            },
            {
              _id: '2',
              firstName: 'Michael',
              lastName: 'Smith',
              dateOfBirth: new Date('1990-03-22').toISOString(),
              gender: 'male',
              bio: 'Chef at a local bistro. Love creating new recipes and sharing them with others.',
              interests: ['cooking', 'hiking', 'farmers markets', 'craft beer'],
              profilePictures: ['https://images.unsplash.com/photo-1500648767791-00dcc994a43e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1587&q=80'],
              dietaryPreferences: ['no restrictions'],
              distance: 3,
              age: 33
            },
            {
              _id: '3',
              firstName: 'Sarah',
              lastName: 'Johnson',
              dateOfBirth: new Date('1992-11-15').toISOString(),
              gender: 'female',
              bio: 'Foodie who appreciates good company and good meals. I love exploring new restaurants and cooking for friends.',
              interests: ['baking', 'yoga', 'food photography', 'reading'],
              profilePictures: ['https://images.unsplash.com/photo-1438761681033-6461ffad8d80?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80'],
              dietaryPreferences: ['vegetarian'],
              distance: 8,
              age: 31
            }
          ]);
        }, 1500);
      });

      const response = await mockAPI;
      setPotentialMatches(response);
      if (response.length > 0) {
        setCurrentMatch(response[0]);
      }
    } catch (err) {
      console.error('Error fetching matches:', err);
      setError('Failed to load potential matches. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async () => {
    if (!currentMatch || actionInProgress) return;
    
    setActionInProgress(true);
    
    try {
      // In a real app, send a request to your API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Remove the current match from the list and show the next one
      handleNextMatch();
      
      // Show some feedback (in a real app, you might want to show a match notification)
      console.log(`Liked ${currentMatch.firstName}`);
    } catch (err) {
      setError('Failed to like this profile. Please try again.');
    } finally {
      setActionInProgress(false);
    }
  };

  const handlePass = async () => {
    if (!currentMatch || actionInProgress) return;
    
    setActionInProgress(true);
    
    try {
      // In a real app, you might want to record this preference
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Show the next match
      handleNextMatch();
    } catch (err) {
      setError('Failed to pass this profile. Please try again.');
    } finally {
      setActionInProgress(false);
    }
  };

  const handleNextMatch = () => {
    if (potentialMatches.length <= 1) {
      // Last match in the list
      setPotentialMatches([]);
      setCurrentMatch(null);
    } else {
      // Remove the first match and set the next one as current
      const updatedMatches = potentialMatches.slice(1);
      setPotentialMatches(updatedMatches);
      setCurrentMatch(updatedMatches[0]);
    }
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
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        
        {!currentMatch && potentialMatches.length === 0 ? (
          <Paper elevation={2} sx={{ p: 4, borderRadius: 2, textAlign: 'center' }}>
            <RestaurantIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
            <Typography variant="h5" gutterBottom>
              No More Profiles
            </Typography>
            <Typography variant="body1" paragraph>
              You've gone through all potential matches for now. Check back later for new profiles!
            </Typography>
            <Button 
              variant="contained" 
              onClick={fetchPotentialMatches}
              startIcon={<RestaurantIcon />}
            >
              Refresh
            </Button>
          </Paper>
        ) : (
          currentMatch && (
            <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
              <CardMedia
                component="img"
                height="400"
                image={currentMatch.profilePictures[0] || 'https://via.placeholder.com/500x400?text=No+Image'}
                alt={`${currentMatch.firstName}'s profile`}
                sx={{ objectFit: 'cover' }}
              />
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box>
                    <Typography variant="h4" component="div">
                      {currentMatch.firstName}, {currentMatch.age}
                    </Typography>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <LocationIcon fontSize="small" color="action" />
                      <Typography variant="body2" color="text.secondary">
                        {currentMatch.distance} miles away
                      </Typography>
                    </Stack>
                  </Box>
                  
                  <Chip 
                    icon={<CakeIcon />}
                    label={currentMatch.gender.charAt(0).toUpperCase() + currentMatch.gender.slice(1)}
                    variant="outlined"
                  />
                </Box>
                
                <Typography variant="body1" sx={{ mt: 2 }}>
                  {currentMatch.bio}
                </Typography>
                
                <Divider sx={{ my: 2 }} />
                
                <Box>
                  <Typography variant="subtitle1" gutterBottom>
                    Interests
                  </Typography>
                  <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                    {currentMatch.interests?.map((interest, index) => (
                      <Chip 
                        key={index}
                        label={interest}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    ))}
                  </Stack>
                </Box>
                
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Dietary Preferences
                  </Typography>
                  <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                    {currentMatch.dietaryPreferences?.map((pref, index) => (
                      <Chip 
                        key={index}
                        icon={<RestaurantIcon />}
                        label={pref.charAt(0).toUpperCase() + pref.slice(1).replace('-', ' ')}
                        size="small"
                        color="secondary"
                      />
                    ))}
                  </Stack>
                </Box>
              </CardContent>
              
              <CardActions sx={{ p: 2, justifyContent: 'center', gap: 3 }}>
                <IconButton 
                  size="large" 
                  onClick={handlePass}
                  disabled={actionInProgress}
                  sx={{ 
                    bgcolor: 'grey.200', 
                    p: 2,
                    '&:hover': { bgcolor: 'grey.300' } 
                  }}
                >
                  <CloseIcon fontSize="large" />
                </IconButton>
                <IconButton 
                  size="large"
                  onClick={handleLike}
                  disabled={actionInProgress}
                  sx={{ 
                    bgcolor: 'primary.light', 
                    color: 'white',
                    p: 2,
                    '&:hover': { bgcolor: 'primary.main' } 
                  }}
                >
                  <FavoriteIcon fontSize="large" />
                </IconButton>
              </CardActions>
            </Card>
          )
        )}
      </Container>
    </>
  );
};

export default Discover;