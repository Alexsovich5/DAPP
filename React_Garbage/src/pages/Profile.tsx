import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Stack,
  Typography,
  Chip
} from '@mui/material';
import {
  Edit as EditIcon,
  Cake as CakeIcon,
  Person as PersonIcon,
  Restaurant as RestaurantIcon,
  LocationOn as LocationIcon,
  Favorite as FavoriteIcon
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import Navigation from '../components/navigation/Navigation';

// Helper function to calculate age from date of birth
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

const Profile: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  if (!user) {
    return (
      <>
        <Navigation />
        <Container>
          <Paper sx={{ p: 3, mt: 3 }}>
            <Typography>User profile not available.</Typography>
          </Paper>
        </Container>
      </>
    );
  }

  return (
    <>
      <Navigation />
      <Container maxWidth="md" sx={{ mt: 4, mb: 10 }}>
        <Paper elevation={2} sx={{ p: { xs: 2, md: 4 }, borderRadius: 2 }}>
          <Box sx={{ position: 'relative' }}>
            <Button
              variant="contained"
              startIcon={<EditIcon />}
              sx={{ position: 'absolute', top: 0, right: 0 }}
              onClick={() => navigate('/edit-profile')}
            >
              Edit Profile
            </Button>
            
            {/* Profile Header */}
            <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, alignItems: 'center', mb: 4 }}>
              <Avatar 
                src={user.profilePicture} 
                alt={user.firstName}
                sx={{ 
                  width: { xs: 120, md: 150 }, 
                  height: { xs: 120, md: 150 },
                  mb: { xs: 2, md: 0 },
                  mr: { md: 4 }
                }}
              />
              <Box>
                <Typography variant="h4" gutterBottom>
                  {user.firstName} {user.lastName}
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center" mb={1}>
                  <CakeIcon color="action" fontSize="small" />
                  <Typography variant="body1" color="text.secondary">
                    {user.dateOfBirth ? `${calculateAge(user.dateOfBirth)} years old` : 'Age not provided'}
                  </Typography>
                </Stack>
                <Stack direction="row" spacing={1} alignItems="center">
                  <PersonIcon color="action" fontSize="small" />
                  <Typography variant="body1" color="text.secondary">
                    {user.gender ? user.gender.charAt(0).toUpperCase() + user.gender.slice(1) : 'Not specified'}
                  </Typography>
                </Stack>
              </Box>
            </Box>
            
            <Divider sx={{ my: 3 }} />
            
            {/* Profile Completion Alert */}
            {!user.isProfileComplete && (
              <Box sx={{ mb: 3 }}>
                <Card sx={{ bgcolor: 'primary.light', color: 'white' }}>
                  <CardContent>
                    <Typography variant="h6">Complete Your Profile</Typography>
                    <Typography variant="body2">
                      Your profile is incomplete. Add more details to increase your chances of finding matches.
                    </Typography>
                    <Button 
                      variant="contained" 
                      color="secondary"
                      sx={{ mt: 2 }}
                      onClick={() => navigate('/edit-profile')}
                    >
                      Complete Profile
                    </Button>
                  </CardContent>
                </Card>
              </Box>
            )}
            
            {/* Profile Details */}
            <Grid container spacing={4}>
              {/* About Me Section */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <FavoriteIcon sx={{ mr: 1 }} /> About Me
                </Typography>
                <Typography variant="body1" paragraph>
                  {user.bio || 'No bio provided yet. Tell others about yourself!'}
                </Typography>
              </Grid>
              
              {/* Interests Section */}
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  My Interests
                </Typography>
                {user.interests && user.interests.length > 0 ? (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {user.interests.map((interest, index) => (
                      <Chip key={index} label={interest} color="primary" variant="outlined" />
                    ))}
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No interests added yet.
                  </Typography>
                )}
              </Grid>
              
              {/* Dietary Preferences Section */}
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <RestaurantIcon sx={{ mr: 1 }} /> Dietary Preferences
                </Typography>
                {user.dietaryPreferences && user.dietaryPreferences.length > 0 ? (
                  <List dense>
                    {user.dietaryPreferences.map((pref, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <RestaurantIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={pref.charAt(0).toUpperCase() + pref.slice(1).replace('-', ' ')} 
                        />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No dietary preferences added yet.
                  </Typography>
                )}
              </Grid>
              
              {/* Location Preferences */}
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <LocationIcon sx={{ mr: 1 }} /> Location
                </Typography>
                {user.locationPreferences?.city ? (
                  <List dense>
                    <ListItem>
                      <ListItemIcon>
                        <LocationIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={user.locationPreferences.city}
                        secondary={`Looking within ${user.locationPreferences.maxDistance || 30} miles`}
                      />
                    </ListItem>
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No location preferences set yet.
                  </Typography>
                )}
              </Grid>
              
              {/* Match Preferences */}
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <FavoriteIcon sx={{ mr: 1 }} /> Looking for
                </Typography>
                {user.matchPreferences?.ageRange || user.matchPreferences?.genders ? (
                  <List dense>
                    {user.matchPreferences.ageRange && (
                      <ListItem>
                        <ListItemIcon>
                          <CakeIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={`Age ${user.matchPreferences.ageRange.min} - ${user.matchPreferences.ageRange.max}`}
                        />
                      </ListItem>
                    )}
                    {user.matchPreferences.genders && user.matchPreferences.genders.length > 0 && (
                      <ListItem>
                        <ListItemIcon>
                          <PersonIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={user.matchPreferences.genders
                            .map(g => g.charAt(0).toUpperCase() + g.slice(1))
                            .join(', ')}
                        />
                      </ListItem>
                    )}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No match preferences set yet.
                  </Typography>
                )}
              </Grid>
            </Grid>
          </Box>
        </Paper>
      </Container>
    </>
  );
};

export default Profile;