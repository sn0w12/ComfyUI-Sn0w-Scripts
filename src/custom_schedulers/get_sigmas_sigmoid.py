import torch

def append_zero(x):
    return torch.cat([x, x.new_zeros([1])])

def get_sigmas_sigmoid(self, n, sigma_max, sigma_min, steepness=10, midpoint_ratio=0.5, device='cpu'):
    """
    Generates 'n' sigmas on an S-curve from sigma_max to sigma_min, with a controllable midpoint.
    
    Args:
    n (int): Number of sigmas to generate.
    sigma_min (float): Minimum value of sigma.
    sigma_max (float): Maximum value of sigma.
    steepness (float): Controls the steepness of the S-curve transition.
    midpoint_ratio (float): Determines where the midpoint of the S-curve is (0 to 1).
    device (str): Device to generate the sigmas on ('cpu' or 'cuda').

    Returns:
    torch.Tensor: A tensor of 'n' sigmas in descending order.
    """
    # Ensure midpoint_ratio is within bounds
    if not (0 <= midpoint_ratio <= 1):
        raise ValueError("midpoint_ratio must be between 0 and 1.")
    
    # Adjust the range of x to skew the sigmoid's midpoint
    midpoint_shift = torch.linspace(-steepness, steepness, n, device=device)
    midpoint_location = -steepness + 2 * steepness * midpoint_ratio
    x = midpoint_shift + (midpoint_location)
    
    # Sigmoid function values
    sigmoids = 1 / (1 + torch.exp(-steepness * (x / steepness)))
    
    # Map the sigmoid output to the range [sigma_max, sigma_min]
    sigmas = append_zero(sigma_max - (sigma_max - sigma_min) * sigmoids)
    
    return (sigmas, )