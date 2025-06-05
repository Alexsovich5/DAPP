import React from 'react';
import { Container, Typography } from '@mui/material';
import Navigation from '../components/navigation/Navigation';

const Preferences: React.FC = () => {
  return (
    <>
      <Navigation />
      <Container>
        <Typography variant="h4">Preferences</Typography>
      </Container>
    </>
  );
};

export default Preferences;