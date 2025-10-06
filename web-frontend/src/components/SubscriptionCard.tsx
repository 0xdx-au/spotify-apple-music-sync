import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Stack,
  LinearProgress,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Star,
  Speed,
  CloudSync,
  Analytics,
  CheckCircle,
  Upgrade,
} from '@mui/icons-material';

interface SubscriptionTier {
  name: string;
  tokens: number;
  price: string;
  features: string[];
  color: string;
}

const subscriptionTiers: SubscriptionTier[] = [
  {
    name: 'Basic',
    tokens: 10,
    price: '$4.99/month',
    features: ['10 sync tokens per month', 'Basic playlist sync', 'Email support'],
    color: '#1976d2',
  },
  {
    name: 'Pro',
    tokens: 50,
    price: '$14.99/month',
    features: ['50 sync tokens per month', 'Priority sync', 'Advanced analytics', 'Live chat support'],
    color: '#1db954',
  },
  {
    name: 'Premium',
    tokens: 200,
    price: '$39.99/month',
    features: ['200 sync tokens per month', 'Unlimited auto-sync', 'Detailed statistics', 'Priority support', 'API access'],
    color: '#ff6b6b',
  },
];

interface SubscriptionCardProps {
  currentPlan?: string;
  tokensRemaining?: number;
  tokensTotal?: number;
  onUpgrade: (tier: string) => void;
}

const SubscriptionCard: React.FC<SubscriptionCardProps> = ({
  currentPlan = 'Basic',
  tokensRemaining = 7,
  tokensTotal = 10,
  onUpgrade,
}) => {
  const currentTier = subscriptionTiers.find(tier => tier.name === currentPlan) || subscriptionTiers[0];
  const tokensUsed = tokensTotal - tokensRemaining;
  const usagePercentage = (tokensUsed / tokensTotal) * 100;

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">
            Subscription Plan
          </Typography>
          <Button
            variant="outlined"
            startIcon={<Upgrade />}
            onClick={() => onUpgrade(currentPlan)}
            size="small"
          >
            Upgrade
          </Button>
        </Box>

        {/* Current Plan */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Chip
              label={currentTier.name}
              sx={{ 
                bgcolor: currentTier.color, 
                color: 'white',
                fontWeight: 600,
              }}
            />
            <Typography variant="body1" color="text.secondary">
              {currentTier.price}
            </Typography>
          </Box>

          {/* Token Usage */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Sync Tokens
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {tokensRemaining}/{tokensTotal} remaining
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={100 - usagePercentage}
              sx={{
                height: 8,
                borderRadius: 4,
                bgcolor: 'rgba(255,255,255,0.1)',
                '& .MuiLinearProgress-bar': {
                  bgcolor: usagePercentage > 80 ? '#ff6b6b' : usagePercentage > 60 ? '#ffa726' : '#1db954',
                },
              }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              Resets monthly
            </Typography>
          </Box>
        </Box>

        <Divider sx={{ mb: 2 }} />

        {/* Plan Features */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" fontWeight={600} gutterBottom>
            Your Plan Includes:
          </Typography>
          <List dense sx={{ py: 0 }}>
            {currentTier.features.map((feature, index) => (
              <ListItem key={index} sx={{ py: 0.5, px: 0 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <CheckCircle sx={{ fontSize: 16, color: currentTier.color }} />
                </ListItemIcon>
                <ListItemText 
                  primary={feature}
                  primaryTypographyProps={{ variant: 'body2' }}
                />
              </ListItem>
            ))}
          </List>
        </Box>

        {/* Usage Stats */}
        <Box>
          <Typography variant="body2" fontWeight={600} gutterBottom>
            This Month:
          </Typography>
          <Stack direction="row" spacing={3} sx={{ mt: 1 }}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="primary">
                {tokensUsed}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Syncs Used
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="success.main">
                247
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Tracks Synced
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="info.main">
                12
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Playlists Synced
              </Typography>
            </Box>
          </Stack>
        </Box>

        {/* Low tokens warning */}
        {tokensRemaining <= 2 && (
          <Box sx={{ mt: 2, p: 2, bgcolor: 'warning.main', borderRadius: 2 }}>
            <Typography variant="body2" color="warning.contrastText">
              <strong>Running low on sync tokens!</strong> Consider upgrading your plan to continue syncing.
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default SubscriptionCard;