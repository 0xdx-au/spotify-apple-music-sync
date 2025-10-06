import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Slider,
  Stack,
  Chip,
  Divider,
  Alert,
} from '@mui/material';
import {
  AccessTime,
  PhoneAndroid,
  Computer,
  TabletMac,
} from '@mui/icons-material';

interface TimeEstimate {
  device: string;
  icon: React.ReactNode;
  baseTimePerTrack: number; // seconds
  description: string;
}

const deviceEstimates: TimeEstimate[] = [
  {
    device: 'Phone',
    icon: <PhoneAndroid />,
    baseTimePerTrack: 15,
    description: 'Mobile app, touch interface',
  },
  {
    device: 'Computer',
    icon: <Computer />,
    baseTimePerTrack: 8,
    description: 'Desktop/laptop with keyboard',
  },
  {
    device: 'Tablet',
    icon: <TabletMac />,
    baseTimePerTrack: 12,
    description: 'Tablet with touch interface',
  },
];

interface TimeEstimateCardProps {
  totalTracks?: number;
}

const TimeEstimateCard: React.FC<TimeEstimateCardProps> = ({
  totalTracks: initialTracks = 50,
}) => {
  const [trackCount, setTrackCount] = useState(initialTracks);

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const getEfficiencyMessage = (totalMinutes: number): { message: string; severity: 'info' | 'warning' | 'error' } => {
    if (totalMinutes < 5) {
      return { message: "Quick sync! This won't take long.", severity: 'info' };
    } else if (totalMinutes < 30) {
      return { message: "Moderate time investment. Perfect for a coffee break!", severity: 'info' };
    } else if (totalMinutes < 120) {
      return { message: "Significant time required. Consider doing this during downtime.", severity: 'warning' };
    } else {
      return { message: "This would take hours! Our service saves you massive amounts of time.", severity: 'error' };
    }
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <AccessTime color="primary" />
          <Typography variant="h6">
            Manual Sync Time Calculator
          </Typography>
        </Box>

        {/* Track Count Slider */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Number of tracks to sync
          </Typography>
          <Slider
            value={trackCount}
            onChange={(_, value) => setTrackCount(value as number)}
            min={1}
            max={1000}
            step={5}
            marks={[
              { value: 1, label: '1' },
              { value: 50, label: '50' },
              { value: 250, label: '250' },
              { value: 500, label: '500' },
              { value: 1000, label: '1000' },
            ]}
            valueLabelDisplay="on"
            sx={{ mt: 2 }}
          />
        </Box>

        <Typography variant="body1" fontWeight={600} gutterBottom>
          Estimated manual sync time:
        </Typography>

        {/* Time Estimates */}
        <Stack spacing={2} sx={{ mb: 3 }}>
          {deviceEstimates.map((estimate) => {
            const totalSeconds = trackCount * estimate.baseTimePerTrack;
            const totalMinutes = Math.floor(totalSeconds / 60);
            
            return (
              <Box
                key={estimate.device}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  p: 2,
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 2,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  {estimate.icon}
                  <Box>
                    <Typography variant="body1" fontWeight={600}>
                      {estimate.device}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {estimate.description}
                    </Typography>
                  </Box>
                </Box>
                
                <Box sx={{ textAlign: 'right' }}>
                  <Chip
                    label={formatTime(totalSeconds)}
                    color={totalMinutes > 60 ? 'error' : totalMinutes > 20 ? 'warning' : 'success'}
                    variant="outlined"
                  />
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                    ~{estimate.baseTimePerTrack}s per track
                  </Typography>
                </Box>
              </Box>
            );
          })}
        </Stack>

        <Divider sx={{ mb: 2 }} />

        {/* Efficiency Message */}
        <Box sx={{ mb: 2 }}>
          <Alert 
            severity={getEfficiencyMessage(Math.floor(trackCount * deviceEstimates[1].baseTimePerTrack / 60)).severity}
            variant="outlined"
          >
            {getEfficiencyMessage(Math.floor(trackCount * deviceEstimates[1].baseTimePerTrack / 60)).message}
          </Alert>
        </Box>

        {/* Our Service Comparison */}
        <Box sx={{ p: 2, bgcolor: 'primary.main', borderRadius: 2, color: 'primary.contrastText' }}>
          <Typography variant="body1" fontWeight={600} gutterBottom>
            With our service: ~30 seconds ⚡
          </Typography>
          <Typography variant="body2">
            We sync {trackCount} tracks automatically while you grab a coffee!
          </Typography>
        </Box>

        {/* Additional Stats */}
        <Box sx={{ mt: 3, pt: 2, borderTop: 1, borderColor: 'divider' }}>
          <Stack direction="row" spacing={3} justifyContent="center">
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="error.main">
                {Math.floor(trackCount * deviceEstimates[0].baseTimePerTrack / 3600)}+
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Hours saved (mobile)
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="success.main">
                99.8%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Time savings
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="info.main">
                0
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Manual errors
              </Typography>
            </Box>
          </Stack>
        </Box>
      </CardContent>
    </Card>
  );
};

export default TimeEstimateCard;