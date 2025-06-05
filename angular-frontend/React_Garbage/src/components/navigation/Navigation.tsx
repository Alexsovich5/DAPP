import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  AppBar,
  Box,
  Toolbar,
  IconButton,
  Typography,
  Menu,
  Container,
  Avatar,
  Button,
  Tooltip,
  MenuItem,
  Badge,
  BottomNavigation,
  BottomNavigationAction,
  Paper
} from '@mui/material';
import {
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  Restaurant as RestaurantIcon,
  Favorite as FavoriteIcon,
  Chat as ChatIcon,
  Person as PersonIcon
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';

// Logo component
const Logo: React.FC = () => (
  <Typography
    variant="h6"
    noWrap
    component="div"
    sx={{
      mr: 2,
      display: { xs: 'none', md: 'flex' },
      fontFamily: 'monospace',
      fontWeight: 700,
      letterSpacing: '.3rem',
      color: 'inherit',
      textDecoration: 'none',
    }}
  >
    DINNER1
  </Typography>
);

const Navigation: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [anchorElUser, setAnchorElUser] = useState<null | HTMLElement>(null);
  const [value, setValue] = useState(getActiveTabFromPath(location.pathname));

  function getActiveTabFromPath(path: string): number {
    if (path.includes('/discover')) return 0;
    if (path.includes('/matches')) return 1;
    if (path.includes('/chat')) return 2;
    if (path.includes('/profile')) return 3;
    return 0;
  }

  const handleOpenUserMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorElUser(event.currentTarget);
  };

  const handleCloseUserMenu = () => {
    setAnchorElUser(null);
  };

  const handleNavigate = (path: string) => {
    navigate(path);
    handleCloseUserMenu();
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
    handleCloseUserMenu();
  };

  const handleBottomNavChange = (_event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
    switch (newValue) {
      case 0:
        navigate('/discover');
        break;
      case 1:
        navigate('/matches');
        break;
      case 2:
        navigate('/chat');
        break;
      case 3:
        navigate('/profile');
        break;
      default:
        navigate('/discover');
    }
  };

  if (!isAuthenticated) {
    return (
      <AppBar position="static">
        <Container maxWidth="xl">
          <Toolbar disableGutters>
            <Logo />
            <Box sx={{ flexGrow: 1, display: { xs: 'flex', md: 'none' } }}>
              <Typography
                variant="h5"
                noWrap
                component="div"
                sx={{
                  mr: 2,
                  display: { xs: 'flex', md: 'none' },
                  flexGrow: 1,
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  letterSpacing: '.3rem',
                  color: 'inherit',
                  textDecoration: 'none',
                }}
              >
                DINNER1
              </Typography>
            </Box>
            <Box sx={{ flexGrow: 1 }} />
            <Box sx={{ display: 'flex' }}>
              <Button
                onClick={() => navigate('/login')}
                sx={{ my: 2, color: 'white', display: 'block' }}
                aria-label="Sign in"
              >
                Login
              </Button>
              <Button
                onClick={() => navigate('/register')}
                sx={{ my: 2, color: 'white', display: 'block' }}
                aria-label="Create account"
              >
                Register
              </Button>
            </Box>
          </Toolbar>
        </Container>
      </AppBar>
    );
  }

  return (
    <>
      <AppBar position="static">
        <Container maxWidth="xl">
          <Toolbar disableGutters>
            <Logo />
            
            <Box sx={{ flexGrow: 1, display: { xs: 'flex', md: 'none' } }}>
              <IconButton
                size="large"
                aria-label="navigation menu"
                aria-controls="menu-mobile"
                aria-haspopup="true"
                onClick={handleOpenUserMenu}
                color="inherit"
              >
                <MenuIcon />
              </IconButton>
            </Box>

            {isAuthenticated ? (
              <>
                <Box sx={{ flexGrow: 1 }} />
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <IconButton 
                    color="inherit"
                    aria-label="notifications"
                    onClick={() => navigate('/notifications')}
                  >
                    <Badge badgeContent={4} color="error">
                      <NotificationsIcon />
                    </Badge>
                  </IconButton>
                  
                  <Tooltip title="Open user menu">
                    <IconButton
                      onClick={handleOpenUserMenu}
                      sx={{ ml: 2 }}
                      aria-label="user menu"
                      aria-controls="user-menu"
                      aria-haspopup="true"
                    >
                      <Avatar alt={user?.firstName} src={user?.profilePicture} />
                    </IconButton>
                  </Tooltip>
                  
                  <Menu
                    id="user-menu"
                    anchorEl={anchorElUser}
                    anchorOrigin={{
                      vertical: 'bottom',
                      horizontal: 'right',
                    }}
                    keepMounted
                    transformOrigin={{
                      vertical: 'top',
                      horizontal: 'right',
                    }}
                    open={Boolean(anchorElUser)}
                    onClose={handleCloseUserMenu}
                  >
                    <MenuItem onClick={() => handleNavigate('/profile')} aria-label="View profile">
                      <Typography textAlign="center">Profile</Typography>
                    </MenuItem>
                    <MenuItem onClick={() => handleNavigate('/edit-profile')} aria-label="View settings">
                      <Typography textAlign="center">Edit Profile</Typography>
                    </MenuItem>
                    <MenuItem onClick={() => handleNavigate('/preferences')} aria-label="View settings">
                      <Typography textAlign="center">Preferences</Typography>
                    </MenuItem>
                    <MenuItem onClick={handleLogout} aria-label="Sign out">
                      <Typography textAlign="center">Logout</Typography>
                    </MenuItem>
                  </Menu>
                </Box>
              </>
            ) : (
              <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  onClick={() => navigate('/login')}
                  sx={{ my: 2, color: 'white', display: 'block' }}
                  aria-label="Sign in"
                >
                  Login
                </Button>
                <Button
                  onClick={() => navigate('/register')}
                  sx={{ my: 2, color: 'white', display: 'block' }}
                  aria-label="Create account"
                >
                  Register
                </Button>
              </Box>
            )}
          </Toolbar>
        </Container>
      </AppBar>
      
      {isAuthenticated && (
        <Paper sx={{ position: 'fixed', bottom: 0, left: 0, right: 0 }} elevation={3}>
          <BottomNavigation
            value={value}
            onChange={handleBottomNavChange}
            showLabels
            sx={{ borderTop: 1, borderColor: 'divider' }}
          >
            <BottomNavigationAction 
              label="Discover" 
              icon={<RestaurantIcon />} 
              aria-label="Discover matches"
            />
            <BottomNavigationAction 
              label="Matches" 
              icon={<FavoriteIcon />}
              aria-label="View matches"
            />
            <BottomNavigationAction 
              label="Messages" 
              icon={<ChatIcon />}
              aria-label="View messages"
            />
            <BottomNavigationAction 
              label="Profile" 
              icon={<PersonIcon />}
              aria-label="View profile"
            />
          </BottomNavigation>
        </Paper>
      )}
    </>
  );
};

export default Navigation;