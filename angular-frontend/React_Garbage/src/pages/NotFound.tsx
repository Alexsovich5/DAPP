import React from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Button,
  Paper
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/navigation/Navigation';

const NotFound: React.FC = () => {
  const navigate = useNavigate();

  return (
    <>
      <Navigation />
      <Container maxWidth="md">
        <Paper 
          elevation={3} 
          sx={{ 
            p: 4, 
            mt: 8, 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center',
            textAlign: 'center'
          }}
        >
          <Typography variant="h1" color="primary" sx={{ fontWeight: 'bold', fontSize: { xs: '4rem', md: '6rem' } }}>
            404
          </Typography>
          
          <Typography variant="h4" gutterBottom sx={{ mt: 2 }}>
            Page Not Found
          </Typography>
          
          <Typography variant="body1" color="text.secondary" sx={{ mt: 2, mb: 4 }}>
            The page you are looking for doesn't exist or has been moved.
          </Typography>
          
          <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
            <Button 
              variant="contained" 
              color="primary" 
              onClick={() => navigate('/')}
              size="large"
            >
              Go to Home
            </Button>
            <Button 
              variant="outlined" 
              onClick={() => navigate(-1)}
              size="large"
            >
              Go Back
            </Button>
          </Box>
        </Paper>
      </Container>
    </>
  );
};

export default NotFound;