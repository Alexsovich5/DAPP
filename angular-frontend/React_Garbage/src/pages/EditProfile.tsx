import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Avatar,
  Box,
  Button,
  Container,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Slider,
  Stack,
  TextField,
  Typography,
  Chip,
  FormHelperText,
  Alert,
  CircularProgress
} from '@mui/material';
import { 
  PhotoCamera as PhotoCameraIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { useFormik } from 'formik';
import * as yup from 'yup';
import { useAuth } from '../context/AuthContext';
import Navigation from '../components/navigation/Navigation';
import { debounce } from 'lodash';
import { SelectChangeEvent } from '@mui/material/Select';

// Define validation schema
const validationSchema = yup.object({
  firstName: yup.string().required('First name is required'),
  lastName: yup.string().required('Last name is required'),
  bio: yup.string().max(500, 'Bio must be 500 characters or less'),
  minAge: yup.number().min(18, 'Minimum age must be at least 18'),
  maxAge: yup.number().max(99, 'Maximum age must be 99 or less')
    .moreThan(yup.ref('minAge'), 'Maximum age must be greater than minimum age'),
  maxDistance: yup.number().min(5, 'Minimum distance is 5 miles')
    .max(100, 'Maximum distance is 100 miles')
});

// Dietary preferences options
const dietaryOptions = [
  'vegetarian',
  'vegan',
  'pescatarian',
  'gluten-free',
  'dairy-free',
  'kosher',
  'halal',
  'keto',
  'paleo',
  'no restrictions',
  'other'
];

// Gender options
const genderOptions = [
  'male',
  'female',
  'non-binary'
];

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  profilePicture?: string;
  bio?: string; // User's biography or description
  interests?: string[];
  dietaryPreferences?: string[];
  locationPreferences?: {
    city?: string;
    maxDistance?: number;
    coordinates?: {
      latitude: number;
      longitude: number;
    };
  };
  matchPreferences?: {
    ageRange?: {
      min: number;
      max: number;
    };
    genders?: string[];
  };
}

interface EditProfileFormValues {
  firstName: string;
  lastName: string;
  bio: string;
  interests: string[];
  dietaryPreferences: string[];
  city: string;
  maxDistance: number;
  minAge: number;
  maxAge: number;
  genderPreferences: string[];
}

const EditProfile: React.FC = () => {
  const { user, updateProfile, error, clearError, isLoading } = useAuth();
  const navigate = useNavigate();
  
  const [newInterest, setNewInterest] = useState('');
  const [serverError, setServerError] = useState<string | null>(null);
  const [isImageUploading, setIsImageUploading] = useState(false);
  
  const formik = useFormik<EditProfileFormValues>({
    initialValues: {
      firstName: user?.firstName ?? '',
      lastName: user?.lastName ?? '',
      bio: user?.bio ?? '',
      interests: user?.interests ?? [],
      dietaryPreferences: user?.dietaryPreferences ?? [],
      city: user?.locationPreferences?.city ?? '',
      maxDistance: user?.locationPreferences?.maxDistance ?? 30,
      minAge: user?.matchPreferences?.ageRange?.min ?? 21,
      maxAge: user?.matchPreferences?.ageRange?.max ?? 65,
      genderPreferences: user?.matchPreferences?.genders ?? [],
    },
    validationSchema,
    onSubmit: async (values) => {
      setServerError(null);
      clearError();
      
      try {
        const updatedProfile = {
          firstName: values.firstName,
          lastName: values.lastName,
          bio: values.bio,
          interests: values.interests,
          dietaryPreferences: values.dietaryPreferences,
          locationPreferences: {
            city: values.city,
            maxDistance: values.maxDistance,
            coordinates: user?.locationPreferences?.coordinates ?? { latitude: 0, longitude: 0 }
          },
          matchPreferences: {
            ageRange: {
              min: values.minAge,
              max: values.maxAge
            },
            genders: values.genderPreferences
          }
        };
        
        await updateProfile(updatedProfile);
        navigate('/profile');
      } catch (err: unknown) {
        console.error('Error updating profile:', err);
        setServerError('Failed to update profile. Please try again later.');
      }
    },
  });

  // Debounced form change handler
  const debouncedHandleChange = debounce((event: React.ChangeEvent<any> | SelectChangeEvent<string[]>) => {
    formik.handleChange(event);
  }, 300);

  const handleAddInterest = () => {
    if (newInterest.trim() && !formik.values.interests.includes(newInterest.trim())) {
      formik.setFieldValue('interests', [...formik.values.interests, newInterest.trim()]);
      setNewInterest('');
    }
  };

  const handleDeleteInterest = (interestToDelete: string) => {
    formik.setFieldValue(
      'interests',
      formik.values.interests.filter((interest: string) => interest !== interestToDelete)
    );
  };

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsImageUploading(true);

    try {
      // Simulated API call to upload image
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const imageUrl = URL.createObjectURL(file);
      await updateProfile({ profilePicture: imageUrl });
    } catch (err) {
      console.error('Image upload error:', err);
      if (err instanceof Error) {
        setServerError(`Failed to upload image: ${err.message}`);
      } else {
        setServerError('Failed to upload image. Please try again.');
      }
    } finally {
      setIsImageUploading(false);
    }
  };

  return (
    <>
      <Navigation />
      <Container maxWidth="md" sx={{ mt: 4, mb: 10 }}>
        <Paper elevation={2} sx={{ p: { xs: 2, md: 4 }, borderRadius: 2 }}>
          <Typography variant="h4" gutterBottom>
            Edit Profile
          </Typography>
          
          {(error ?? serverError) && (
            <Alert 
              severity="error" 
              sx={{ mb: 3 }}
              onClose={() => {
                clearError();
                setServerError(null);
              }}
            >
              {error ?? serverError}
            </Alert>
          )}
          
          <Box component="form" onSubmit={formik.handleSubmit}>
            {/* Profile Picture */}
            <Box sx={{ mb: 4, textAlign: 'center' }}>
              <Avatar
                src={user?.profilePicture}
                alt={user?.firstName}
                sx={{
                  width: 150,
                  height: 150,
                  mx: 'auto',
                  mb: 2,
                  boxShadow: 2
                }}
              />
              <Stack direction="row" justifyContent="center">
                <Button
                  variant="outlined"
                  component="label"
                  startIcon={<PhotoCameraIcon />}
                  disabled={isImageUploading}
                >
                  {isImageUploading ? <CircularProgress size={24} /> : 'Upload Photo'}
                  <input
                    hidden
                    accept="image/*"
                    type="file"
                    onChange={handleImageUpload}
                    disabled={isImageUploading}
                  />
                </Button>
              </Stack>
            </Box>
            
            <Divider sx={{ my: 3 }} />
            
            {/* Basic Information */}
            <Typography variant="h6" gutterBottom>
              Basic Information
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  id="firstName"
                  name="firstName"
                  label="First Name"
                  value={formik.values.firstName}
                  onChange={debouncedHandleChange}
                  onBlur={formik.handleBlur}
                  error={formik.touched.firstName && Boolean(formik.errors.firstName)}
                  helperText={formik.touched.firstName && formik.errors.firstName}
                  disabled={isLoading}
                  aria-label="First Name"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  id="lastName"
                  name="lastName"
                  label="Last Name"
                  value={formik.values.lastName}
                  onChange={debouncedHandleChange}
                  onBlur={formik.handleBlur}
                  error={formik.touched.lastName && Boolean(formik.errors.lastName)}
                  helperText={formik.touched.lastName && formik.errors.lastName}
                  disabled={isLoading}
                  aria-label="Last Name"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  id="bio"
                  name="bio"
                  label="Bio"
                  multiline
                  rows={4}
                  value={formik.values.bio}
                  onChange={debouncedHandleChange}
                  onBlur={formik.handleBlur}
                  error={formik.touched.bio && Boolean(formik.errors.bio)}
                  helperText={
                    (formik.touched.bio && formik.errors.bio) || 
                    `${formik.values.bio.length}/500 characters`
                  }
                  disabled={isLoading}
                  aria-label="Bio"
                />
              </Grid>
            </Grid>
            
            <Divider sx={{ my: 3 }} />
            
            {/* Interests */}
            <Typography variant="h6" gutterBottom>
              Interests
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                  <TextField
                    fullWidth
                    label="Add Interest"
                    value={newInterest}
                    onChange={(e) => setNewInterest(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddInterest();
                      }
                    }}
                    disabled={isLoading}
                    aria-label="Add Interest"
                  />
                  <Button
                    onClick={handleAddInterest}
                    variant="contained"
                    disabled={!newInterest.trim() || isLoading}
                    startIcon={<AddIcon />}
                  >
                    Add
                  </Button>
                </Stack>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {formik.values.interests.map((interest) => (
                    <Chip
                      key={interest}
                      label={interest}
                      onDelete={() => handleDeleteInterest(interest)}
                      color="primary"
                      variant="outlined"
                      disabled={isLoading}
                    />
                  ))}
                </Box>
                {formik.values.interests.length === 0 && (
                  <Typography variant="body2" color="text.secondary">
                    Add some interests to help us match you with like-minded people.
                  </Typography>
                )}
              </Grid>
            </Grid>
            
            <Divider sx={{ my: 3 }} />
            
            {/* Dietary Preferences */}
            <Typography variant="h6" gutterBottom>
              Dietary Preferences
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel id="dietary-preferences-label">
                    Dietary Preferences
                  </InputLabel>
                  <Select
                    labelId="dietary-preferences-label"
                    id="dietaryPreferences"
                    name="dietaryPreferences"
                    multiple
                    value={formik.values.dietaryPreferences}
                    onChange={debouncedHandleChange}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => (
                          <Chip key={value} label={value} />
                        ))}
                      </Box>
                    )}
                    disabled={isLoading}
                    aria-label="Dietary Preferences"
                  >
                    {dietaryOptions.map((option) => (
                      <MenuItem key={option} value={option}>
                        {option.charAt(0).toUpperCase() + option.slice(1)}
                      </MenuItem>
                    ))}
                  </Select>
                  <FormHelperText>
                    Select all that apply to you
                  </FormHelperText>
                </FormControl>
              </Grid>
            </Grid>
            
            <Divider sx={{ my: 3 }} />
            
            {/* Location Preferences */}
            <Typography variant="h6" gutterBottom>
              Location
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  id="city"
                  name="city"
                  label="City"
                  value={formik.values.city}
                  onChange={debouncedHandleChange}
                  disabled={isLoading}
                  aria-label="City"
                />
              </Grid>
              <Grid item xs={12}>
                <Typography id="max-distance-label" gutterBottom>
                  Maximum Distance: {formik.values.maxDistance} miles
                </Typography>
                <Slider
                  name="maxDistance"
                  value={formik.values.maxDistance}
                  onChange={(_, value) => 
                    formik.setFieldValue('maxDistance', value)
                  }
                  step={5}
                  min={5}
                  max={100}
                  valueLabelDisplay="auto"
                  aria-labelledby="max-distance-label"
                  disabled={isLoading}
                />
              </Grid>
            </Grid>
            
            <Divider sx={{ my: 3 }} />
            
            {/* Match Preferences */}
            <Typography variant="h6" gutterBottom>
              Match Preferences
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel id="gender-preferences-label">
                    I am interested in
                  </InputLabel>
                  <Select
                    labelId="gender-preferences-label"
                    id="genderPreferences"
                    name="genderPreferences"
                    multiple
                    value={formik.values.genderPreferences}
                    onChange={debouncedHandleChange}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => (
                          <Chip key={value} label={value} />
                        ))}
                      </Box>
                    )}
                    disabled={isLoading}
                    aria-label="Gender Preferences"
                  >
                    {genderOptions.map((option) => (
                      <MenuItem key={option} value={option}>
                        {option.charAt(0).toUpperCase() + option.slice(1)}
                      </MenuItem>
                    ))}
                  </Select>
                  <FormHelperText>
                    Select all that apply
                  </FormHelperText>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <Typography gutterBottom>
                  Age Range: {formik.values.minAge} - {formik.values.maxAge}
                </Typography>
                <Box sx={{ px: 1 }}>
                  <Slider
                    value={[formik.values.minAge, formik.values.maxAge]}
                    onChange={(_, value) => {
                      const [min, max] = value as number[];
                      formik.setFieldValue('minAge', min);
                      formik.setFieldValue('maxAge', max);
                    }}
                    min={18}
                    max={99}
                    step={1}
                    valueLabelDisplay="auto"
                    disabled={isLoading}
                  />
                </Box>
              </Grid>
            </Grid>
            
            <Box sx={{ mt: 4, display: 'flex', justifyContent: 'space-between' }}>
              <Button
                variant="outlined"
                onClick={() => navigate('/profile')}
                disabled={isLoading}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                disabled={isLoading || !formik.isValid || !formik.dirty}
              >
                {isLoading ? <CircularProgress size={24} /> : 'Save Changes'}
              </Button>
            </Box>
          </Box>
        </Paper>
      </Container>
    </>
  );
};

export default EditProfile;