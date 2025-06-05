import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Grid,
  Link,
  Paper,
  Stack,
  Typography,
  useMediaQuery,
  useTheme
} from '@mui/material';
import {
  Restaurant as RestaurantIcon,
  Favorite as FavoriteIcon,
  Chat as ChatIcon,
  LocationOn as LocationIcon
} from '@mui/icons-material';

const Landing: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  return (
    <Box>
      {/* Hero Section */}
      <Box
        sx={{
          backgroundColor: 'primary.main',
          color: 'white',
          pt: { xs: 8, md: 12 },
          pb: { xs: 10, md: 14 },
          position: 'relative',
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography
                variant="h2"
                component="h1"
                sx={{
                  fontWeight: 'bold',
                  mb: 2,
                  fontSize: { xs: '2.5rem', md: '3.5rem' }
                }}
              >
                Find Your Perfect Dinner Date
              </Typography>
              <Typography
                variant="h5"
                component="p"
                sx={{ mb: 4, opacity: 0.9 }}
              >
                Connect with people who share your culinary interests and discover new restaurants together.
              </Typography>
              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                spacing={2}
              >
                <Button
                  component={RouterLink}
                  to="/register"
                  variant="contained"
                  color="secondary"
                  size="large"
                  sx={{ 
                    py: 1.5,
                    px: 4,
                    fontSize: '1.1rem'
                  }}
                >
                  Join Now
                </Button>
                <Button
                  component={RouterLink}
                  to="/login"
                  variant="outlined"
                  color="inherit"
                  size="large"
                  sx={{ 
                    py: 1.5,
                    px: 4,
                    fontSize: '1.1rem',
                    borderColor: 'white',
                    '&:hover': {
                      borderColor: 'white',
                      backgroundColor: 'rgba(255,255,255,0.1)'
                    }
                  }}
                >
                  Sign In
                </Button>
              </Stack>
            </Grid>
            <Grid 
              item 
              xs={12} 
              md={6} 
              sx={{ 
                display: { xs: 'none', md: 'block' } 
              }}
            >
              <Box
                component="img"
                src="https://images.unsplash.com/photo-1529156069898-49953e39b3ac?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2532&q=80"
                alt="Couple enjoying dinner"
                sx={{
                  width: '100%',
                  height: 'auto',
                  borderRadius: 4,
                  boxShadow: 8,
                  transform: 'rotate(2deg)'
                }}
              />
            </Grid>
          </Grid>
        </Container>
        
        {/* Wave shape divider */}
        <Box
          component="svg"
          preserveAspectRatio="none"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 1440 74"
          sx={{
            position: 'absolute',
            bottom: -1,
            left: 0,
            width: '100%',
            height: { xs: 40, md: 74 },
            path: {
              fill: 'white',
            },
          }}
        >
          <path d="M456.464 0.0433865C277.158 -1.70575 0 50.0141 0 50.0141V74H1440V50.0141C1440 50.0141 1320.4 31.1925 1243.09 27.0276C1099.33 19.2816 1019.08 53.1981 875.138 50.0141C710.527 46.3727 621.108 1.64949 456.464 0.0433865Z"></path>
        </Box>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: { xs: 8, md: 12 } }}>
        <Typography
          variant="h3"
          component="h2"
          align="center"
          gutterBottom
          sx={{ mb: 8 }}
        >
          How It Works
        </Typography>

        <Grid container spacing={5}>
          <Grid item xs={12} md={4}>
            <Paper 
              elevation={2} 
              sx={{ 
                p: 4, 
                height: '100%', 
                textAlign: 'center',
                borderRadius: 4,
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-8px)',
                }
              }}
            >
              <FavoriteIcon color="primary" sx={{ fontSize: 60, mb: 2 }} />
              <Typography variant="h5" component="h3" gutterBottom>
                Match with Foodies
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Create a profile and match with people who share your culinary preferences and dietary restrictions.
              </Typography>
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <Paper 
              elevation={2} 
              sx={{ 
                p: 4, 
                height: '100%', 
                textAlign: 'center',
                borderRadius: 4,
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-8px)',
                }
              }}
            >
              <ChatIcon color="primary" sx={{ fontSize: 60, mb: 2 }} />
              <Typography variant="h5" component="h3" gutterBottom>
                Chat & Plan
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Message your matches and discover new restaurants together or plan a dinner date at your favorite spot.
              </Typography>
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <Paper 
              elevation={2} 
              sx={{ 
                p: 4, 
                height: '100%', 
                textAlign: 'center',
                borderRadius: 4,
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-8px)',
                }
              }}
            >
              <RestaurantIcon color="primary" sx={{ fontSize: 60, mb: 2 }} />
              <Typography variant="h5" component="h3" gutterBottom>
                Dine Together
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Meet up for a memorable dining experience with someone who appreciates good food just as much as you do.
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      </Container>

      {/* Testimonials Section */}
      <Box sx={{ bgcolor: 'grey.100', py: { xs: 8, md: 12 } }}>
        <Container maxWidth="md">
          <Typography
            variant="h3"
            component="h2"
            align="center"
            gutterBottom
            sx={{ mb: 8 }}
          >
            Success Stories
          </Typography>

          <Grid container spacing={4}>
            <Grid item xs={12} md={6}>
              <Paper 
                elevation={1} 
                sx={{ 
                  p: 4, 
                  borderRadius: 4,
                  mb: { xs: 0, md: 2 }
                }}
              >
                <Typography variant="body1" paragraph sx={{ fontStyle: 'italic' }}>
                  "I never thought I'd meet someone who loves Thai food as much as I do! We now have weekly date nights trying new restaurants around the city."
                </Typography>
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                  - Sarah & Michael
                </Typography>
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Paper 
                elevation={1} 
                sx={{ 
                  p: 4, 
                  borderRadius: 4,
                  mb: { xs: 0, md: 2 }
                }}
              >
                <Typography variant="body1" paragraph sx={{ fontStyle: 'italic' }}>
                  "As a vegan, it was hard to find someone who understood my dietary choices. Thanks to Dinner1, I found my perfect match who shares my culinary values!"
                </Typography>
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                  - James & Emma
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* CTA Section */}
      <Box 
        sx={{ 
          py: { xs: 8, md: 12 },
          background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)',
          color: 'white',
          textAlign: 'center',
        }}
      >
        <Container maxWidth="md">
          <Typography variant="h3" component="h2" gutterBottom>
            Ready to Find Your Dinner Date?
          </Typography>
          <Typography variant="h6" component="p" sx={{ mb: 4, opacity: 0.9 }}>
            Join thousands of food lovers already connecting through Dinner1
          </Typography>
          <Button
            component={RouterLink}
            to="/register"
            variant="contained"
            color="secondary"
            size="large"
            sx={{ 
              py: 2,
              px: 6,
              fontSize: '1.2rem',
              boxShadow: 4
            }}
          >
            Create Your Free Profile
          </Button>
        </Container>
      </Box>

      {/* Footer */}
      <Box sx={{ bgcolor: 'grey.900', color: 'grey.400', py: 6 }}>
        <Container maxWidth="lg">
          <Grid container spacing={4}>
            <Grid item xs={12} md={4}>
              <Typography variant="h6" color="white" gutterBottom>
                Dinner1
              </Typography>
              <Typography variant="body2" sx={{ mt: 2 }}>
                Connecting food lovers one table at a time. Find your perfect dinner date today!
              </Typography>
            </Grid>
            
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="h6" color="white" gutterBottom>
                Quick Links
              </Typography>
              <Stack spacing={1}>
                <Link component={RouterLink} to="/about" color="inherit">About Us</Link>
                <Link component={RouterLink} to="/privacy" color="inherit">Privacy Policy</Link>
                <Link component={RouterLink} to="/terms" color="inherit">Terms of Service</Link>
                <Link component={RouterLink} to="/contact" color="inherit">Contact Us</Link>
              </Stack>
            </Grid>
            
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="h6" color="white" gutterBottom>
                Connect With Us
              </Typography>
              <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                <Link href="#" color="inherit">
                  <Box component="span" sx={{ display: 'flex' }}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M22 12c0-5.52-4.48-10-10-10S2 6.48 2 12c0 4.84 3.44 8.87 8 9.8V15H8v-3h2V9.5C10 7.57 11.57 6 13.5 6H16v3h-2c-.55 0-1 .45-1 1v2h3v3h-3v6.95c5.05-.5 9-4.76 9-9.95z" />
                    </svg>
                  </Box>
                </Link>
                <Link href="#" color="inherit">
                  <Box component="span" sx={{ display: 'flex' }}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4a5.8 5.8 0 0 1-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8A5.8 5.8 0 0 1 7.8 2m-.2 2A3.6 3.6 0 0 0 4 7.6v8.8A3.6 3.6 0 0 0 7.6 20h8.8a3.6 3.6 0 0 0 3.6-3.6V7.6A3.6 3.6 0 0 0 16.4 4H7.6m9.65 1.5A1.25 1.25 0 0 1 18.5 6.75A1.25 1.25 0 0 1 17.25 8a1.25 1.25 0 0 1-1.25-1.25a1.25 1.25 0 0 1 1.25-1.25M12 7a5 5 0 0 1 5 5a5 5 0 0 1-5 5a5 5 0 0 1-5-5a5 5 0 0 1 5-5m0 2a3 3 0 0 0-3 3a3 3 0 0 0 3 3a3 3 0 0 0 3-3a3 3 0 0 0-3-3z" />
                    </svg>
                  </Box>
                </Link>
                <Link href="#" color="inherit">
                  <Box component="span" sx={{ display: 'flex' }}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M22.46 6c-.77.35-1.6.58-2.46.69c.88-.53 1.56-1.37 1.88-2.38c-.83.5-1.75.85-2.72 1.05C18.37 4.5 17.26 4 16 4c-2.35 0-4.27 1.92-4.27 4.29c0 .34.04.67.11.98C8.28 9.09 5.11 7.38 3 4.79c-.37.63-.58 1.37-.58 2.15c0 1.49.75 2.81 1.91 3.56c-.71 0-1.37-.2-1.95-.5v.03c0 2.08 1.48 3.82 3.44 4.21a4.22 4.22 0 0 1-1.93.07a4.28 4.28 0 0 0 4 2.98a8.521 8.521 0 0 1-5.33 1.84c-.34 0-.68-.02-1.02-.06C3.44 20.29 5.7 21 8.12 21C16 21 20.33 14.46 20.33 8.79c0-.19 0-.37-.01-.56c.84-.6 1.56-1.36 2.14-2.23z" />
                    </svg>
                  </Box>
                </Link>
              </Stack>
            </Grid>
          </Grid>
          <Typography variant="body2" align="center" sx={{ mt: 8 }}>
            &copy; {new Date().getFullYear()} Dinner1. All rights reserved.
          </Typography>
        </Container>
      </Box>
    </Box>
  );
};

export default Landing;