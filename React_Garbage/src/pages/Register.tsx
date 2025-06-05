import React, { useState } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import {
  Avatar,
  Box,
  Button,
  CircularProgress,
  Container,
  Divider,
  Grid,
  Link,
  Paper,
  TextField,
  Typography,
  Alert,
  Stepper,
  Step,
  StepLabel,
  FormControlLabel,
  Checkbox,
  styled
} from '@mui/material';
import {
  PersonAdd as PersonAddIcon,
  Google as GoogleIcon,
  Facebook as FacebookIcon
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { useFormik } from 'formik';
import * as yup from 'yup';

const steps = ['Account Details', 'Personal Information', 'Preferences'];

// Improved age validation - properly calculates 18 years ago
const eighteenYearsAgo = new Date();
eighteenYearsAgo.setFullYear(eighteenYearsAgo.getFullYear() - 18);

// Validation schema
const validationSchema = yup.object({
  email: yup
    .string()
    .email('Enter a valid email')
    .required('Email is required'),
  password: yup
    .string()
    .min(8, 'Password must be at least 8 characters')
    .required('Password is required'),
  confirmPassword: yup
    .string()
    .oneOf([yup.ref('password')], 'Passwords must match')
    .required('Confirm password is required'),
  firstName: yup
    .string()
    .required('First name is required'),
  lastName: yup
    .string()
    .required('Last name is required'),
  birthdate: yup
    .date()
    .max(eighteenYearsAgo, 'Must be at least 18 years old')
    .required('Birth date is required'),
  gender: yup
    .string()
    .required('Gender is required'),
  dietaryPreferences: yup
    .array()
    .of(yup.string())
    .required('Dietary preference is required'),
  cuisinePreferences: yup
    .string()
    .required('Cuisine preference is required'),
  location: yup
    .string()
    .required('Location is required'),
  agreeTerms: yup
    .boolean()
    .oneOf([true], 'You must accept the terms and conditions')
});

interface RegisterFormValues {
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  birthdate: string; // This will be used as dateOfBirth when sending to API
  gender: string;
  dietaryPreferences: string[];
  cuisinePreferences: string;
  location: string;
  lookingFor: string;
  agreeTerms: boolean;
}

const Register: React.FC = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const formik = useFormik<RegisterFormValues>({
    initialValues: {
      email: '',
      password: '',
      confirmPassword: '',
      firstName: '',
      lastName: '',
      birthdate: '',
      gender: '',
      dietaryPreferences: [] as string[], // Change from string to string[]
      cuisinePreferences: '',
      location: '',
      lookingFor: '',
      agreeTerms: false
    },
    validationSchema,
    onSubmit: async (values) => {
      setLoading(true);
      setError(null);
      
      try {
        // Send all relevant user data to the API
        await register({
          email: values.email,
          password: values.password,
          firstName: values.firstName,
          lastName: values.lastName,
          dateOfBirth: values.birthdate,
          gender: values.gender,
          dietaryPreferences: Array.isArray(values.dietaryPreferences)
            ? values.dietaryPreferences
            : [values.dietaryPreferences], // Ensure it's always an array
          cuisinePreferences: values.cuisinePreferences,
          location: values.location,
          lookingFor: values.lookingFor
        });
        
        navigate('/login', { state: { message: 'Registration successful! Please log in.' } });
      } catch (err: unknown) {
        console.error('Registration error:', err);
        setError(err instanceof Error ? err.message : 'Registration failed. Please try again.');
      } finally {
        setLoading(false);
      }
    }
  });

  const handleNext = () => {
    const currentStepFields = getStepFields(activeStep);
    
    // Mark current step fields as touched
    const fieldTouches: Partial<Record<keyof RegisterFormValues, boolean>> = {};
    currentStepFields.forEach(field => {
      fieldTouches[field as keyof RegisterFormValues] = true;
    });
    formik.setTouched(fieldTouches, true);

    // Check if there are any errors in the current step fields
    const hasErrors = currentStepFields.some(field => 
      Boolean(formik.errors[field as keyof RegisterFormValues])
    );
    
    // Only proceed if current step has no errors
    if (!hasErrors) {
      setActiveStep(prev => prev + 1);
      setError(null);
    }
  };

  // Helper function to get fields for current step
  const getStepFields = (step: number) => {
    switch (step) {
      case 0:
        return ['email', 'password', 'confirmPassword'];
      case 1:
        return ['firstName', 'lastName', 'birthdate', 'gender'];
      case 2:
        return ['dietaryPreferences', 'cuisinePreferences', 'location', 'lookingFor', 'agreeTerms'];
      default:
        return [];
    }
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
    setError(null);
  };

  // Styled components
  const HiddenSelect = styled('select')({
    display: 'none'
  });

  return (
    <Container component="main" maxWidth="sm">
      <Paper
        elevation={3}
        sx={{
          marginTop: 8,
          marginBottom: 8,
          padding: 4,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          borderRadius: 2
        }}
      >
        <Avatar sx={{ m: 1, bgcolor: 'primary.main' }}>
          <PersonAddIcon />
        </Avatar>
        <Typography component="h1" variant="h5">
          Create Account
        </Typography>
        
        <Stepper 
          activeStep={activeStep} 
          sx={{ width: '100%', mt: 3, mb: 3 }}
          aria-label="Registration progress"
        >
          {steps.map((label, index) => (
            <Step key={label}>
              <StepLabel>
                <span id={`step-${index}-label`}>{label}</span>
                <HiddenSelect
                  aria-hidden="true"
                  aria-labelledby={`step-${index}-label`}
                  title={`Step ${index + 1}: ${label}`}
                  value={index}
                  onChange={() => {}}
                >
                  <option value={index}>{label}</option>
                </HiddenSelect>
              </StepLabel>
            </Step>
          ))}
        </Stepper>
        
        {error && (
          <Alert severity="error" sx={{ mt: 2, mb: 1, width: '100%' }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        
        <Box component="form" sx={{ mt: 1, width: '100%' }} onSubmit={formik.handleSubmit}>
          {activeStep === 0 && (
            <>
              <TextField
                margin="normal"
                required
                fullWidth
                id="email"
                label="Email Address"
                name="email"
                autoComplete="email"
                autoFocus
                value={formik.values.email}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.email && Boolean(formik.errors.email)}
                helperText={formik.touched.email && formik.errors.email}
                disabled={loading}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="Password"
                type="password"
                id="password"
                autoComplete="new-password"
                value={formik.values.password}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.password && Boolean(formik.errors.password)}
                helperText={formik.touched.password && formik.errors.password}
                disabled={loading}
                inputProps={{ "data-testid": "password-input" }}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                name="confirmPassword"
                label="Confirm Password"
                type="password"
                id="confirmPassword"
                autoComplete="new-password"
                value={formik.values.confirmPassword}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.confirmPassword && Boolean(formik.errors.confirmPassword)}
                helperText={formik.touched.confirmPassword && formik.errors.confirmPassword}
                disabled={loading}
                inputProps={{ "data-testid": "confirm-password-input" }}
              />
            </>
          )}
          
          {activeStep === 1 && (
            <>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    margin="normal"
                    required
                    fullWidth
                    id="firstName"
                    label="First Name"
                    name="firstName"
                    autoComplete="given-name"
                    value={formik.values.firstName}
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    error={formik.touched.firstName && Boolean(formik.errors.firstName)}
                    helperText={formik.touched.firstName && formik.errors.firstName}
                    disabled={loading}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    margin="normal"
                    required
                    fullWidth
                    id="lastName"
                    label="Last Name"
                    name="lastName"
                    autoComplete="family-name"
                    value={formik.values.lastName}
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    error={formik.touched.lastName && Boolean(formik.errors.lastName)}
                    helperText={formik.touched.lastName && formik.errors.lastName}
                    disabled={loading}
                  />
                </Grid>
              </Grid>
              <TextField
                margin="normal"
                required
                fullWidth
                id="birthdate"
                label="Date of Birth"
                name="birthdate"
                type="date"
                InputLabelProps={{ shrink: true }}
                value={formik.values.birthdate}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.birthdate && Boolean(formik.errors.birthdate)}
                helperText={formik.touched.birthdate && formik.errors.birthdate}
                disabled={loading}
              />
              <TextField
                margin="normal"
                required
                select
                fullWidth
                id="gender"
                label="Gender"
                name="gender"
                SelectProps={{ 
                  native: true,
                  'aria-labelledby': 'gender-label',
                  title: 'Select your gender'
                }}
                inputProps={{
                  'aria-label': 'Gender'
                }}
                value={formik.values.gender}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.gender && Boolean(formik.errors.gender)}
                helperText={formik.touched.gender && formik.errors.gender}
                disabled={loading}
              >
                <Typography id="gender-label" sx={{ display: 'none' }}>
                  Select your gender
                </Typography>
                <option value="" aria-label="Select your gender"></option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="non-binary">Non-binary</option>
                <option value="other">Other</option>
                <option value="prefer-not-to-say">Prefer not to say</option>
              </TextField>
            </>
          )}
          
          {activeStep === 2 && (
            <>
              <TextField
                margin="normal"
                required
                select
                fullWidth
                id="dietaryPreferences"
                label="Dietary Preferences"
                name="dietaryPreferences"
                SelectProps={{ 
                  native: true,
                  'aria-labelledby': 'dietary-preferences-label',
                  title: 'Select your dietary preferences'
                }}
                inputProps={{
                  'aria-label': 'Dietary Preferences'
                }}
                value={formik.values.dietaryPreferences}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.dietaryPreferences && Boolean(formik.errors.dietaryPreferences)}
                helperText={formik.touched.dietaryPreferences && formik.errors.dietaryPreferences}
                disabled={loading}
              >
                <Typography id="dietary-preferences-label" sx={{ display: 'none' }}>
                  Select your dietary preferences
                </Typography>
                <option value="" aria-label="Select your dietary preferences"></option>
                <option value="omnivore">Omnivore</option>
                <option value="vegetarian">Vegetarian</option>
                <option value="vegan">Vegan</option>
                <option value="pescatarian">Pescatarian</option>
                <option value="keto">Keto</option>
                <option value="paleo">Paleo</option>
                <option value="gluten-free">Gluten-free</option>
                <option value="other">Other</option>
              </TextField>
              <TextField
                margin="normal"
                required
                select
                fullWidth
                id="cuisinePreferences"
                label="Favorite Cuisine"
                name="cuisinePreferences"
                SelectProps={{ 
                  native: true,
                  'aria-labelledby': 'cuisine-preferences-label',
                  title: 'Select your favorite cuisine'
                }}
                inputProps={{
                  'aria-label': 'Favorite Cuisine'
                }}
                value={formik.values.cuisinePreferences}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.cuisinePreferences && Boolean(formik.errors.cuisinePreferences)}
                helperText={formik.touched.cuisinePreferences && formik.errors.cuisinePreferences}
                disabled={loading}
              >
                <Typography id="cuisine-preferences-label" sx={{ display: 'none' }}>
                  Select your favorite cuisine
                </Typography>
                <option value="" aria-label="Select your favorite cuisine"></option>
                <option value="italian">Italian</option>
                <option value="mexican">Mexican</option>
                <option value="chinese">Chinese</option>
                <option value="japanese">Japanese</option>
                <option value="indian">Indian</option>
                <option value="thai">Thai</option>
                <option value="mediterranean">Mediterranean</option>
                <option value="french">French</option>
                <option value="american">American</option>
                <option value="other">Other</option>
              </TextField>
              <TextField
                margin="normal"
                required
                fullWidth
                id="location"
                label="Location (City)"
                name="location"
                autoComplete="address-level2"
                value={formik.values.location}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.location && Boolean(formik.errors.location)}
                helperText={formik.touched.location && formik.errors.location}
                disabled={loading}
              />
              <TextField
                margin="normal"
                select
                fullWidth
                id="lookingFor"
                label="Looking For"
                name="lookingFor"
                SelectProps={{ 
                  native: true,
                  'aria-labelledby': 'looking-for-label',
                  title: 'Select who you are looking to meet'
                }}
                inputProps={{
                  'aria-label': 'Looking For'
                }}
                value={formik.values.lookingFor}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.lookingFor && Boolean(formik.errors.lookingFor)}
                helperText={formik.touched.lookingFor && formik.errors.lookingFor}
                disabled={loading}
              >
                <Typography id="looking-for-label" sx={{ display: 'none' }}>
                  Select what you are looking for
                </Typography>
                <option value="" aria-label="Select what you are looking for"></option>
                <option value="men">Men</option>
                <option value="women">Women</option>
                <option value="everyone">Everyone</option>
              </TextField>
              <FormControlLabel
                control={
                  <Checkbox
                    name="agreeTerms"
                    color="primary"
                    checked={formik.values.agreeTerms}
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    disabled={loading}
                  />
                }
                label={
                  <Typography variant="body2">
                    I agree to the{' '}
                    <Link component={RouterLink} to="/terms">
                      Terms of Service
                    </Link>{' '}
                    and{' '}
                    <Link component={RouterLink} to="/privacy">
                      Privacy Policy
                    </Link>
                  </Typography>
                }
              />
            </>
          )}
          
          {activeStep === 3 ? (
            <>
              <Alert severity="success" sx={{ mt: 2, mb: 2 }}>
                All steps completed - you're ready to join Dinner1!
              </Alert>
              <Button
                type="submit"
                fullWidth
                variant="contained"
                color="primary"
                disabled={loading}
                sx={{ mt: 2, mb: 2 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Create Account'}
              </Button>
            </>
          ) : (
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
              <Button
                disabled={activeStep === 0 || loading}
                onClick={handleBack}
                variant="outlined"
                data-testid="back-button"
              >
                Back
              </Button>
              <Button
                variant="contained"
                onClick={handleNext}
                disabled={loading}
                data-testid="next-button"
              >
                {activeStep === 2 ? 'Review' : 'Next'}
              </Button>
            </Box>
          )}
          
          {activeStep === 0 && (
            <>
              <Divider sx={{ my: 3 }}>or register with</Divider>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<GoogleIcon />}
                    disabled={loading}
                    sx={{
                      py: 1,
                      color: 'grey.700',
                      borderColor: 'grey.300',
                      '&:hover': {
                        borderColor: 'grey.400',
                        bgcolor: 'grey.50',
                      },
                    }}
                  >
                    Google
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<FacebookIcon />}
                    disabled={loading}
                    sx={{
                      py: 1,
                      color: '#1877F2',
                      borderColor: '#1877F2',
                      '&:hover': {
                        borderColor: '#1877F2',
                        bgcolor: 'rgba(24, 119, 242, 0.04)',
                      },
                    }}
                  >
                    Facebook
                  </Button>
                </Grid>
              </Grid>
            </>
          )}
          
          <Grid container justifyContent="center" sx={{ mt: 3 }}>
            <Grid item>
              <Typography variant="body2">
                Already have an account?{' '}
                <Link component={RouterLink} to="/login" variant="body2">
                  Sign in
                </Link>
              </Typography>
            </Grid>
          </Grid>
        </Box>
      </Paper>
      
      <Box mt={5} textAlign="center">
        <Typography variant="body2" color="text.secondary">
          &copy; {new Date().getFullYear()} Dinner1. All rights reserved.
        </Typography>
      </Box>
    </Container>
  );
};

export default Register;