"""Validation utilities for SCM configuration."""
import logging
from typing import Dict, Set, List, Optional
from ordered_set import OrderedSet
from dynaconf.utils.boxing import DynaBox

from scm_config import defaults
from scm_config import constants


class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass


class RecipeValidator:
    """Validates recipe configurations."""
    
    def __init__(self, recipe_name: str, settings: Dict):
        """
        Initialize the validator.
        
        Args:
            recipe_name: Name of the recipe being validated
            settings: Settings dictionary to validate
        """
        self.recipe_name = recipe_name
        self.settings = settings
        self.errors: List[str] = []
    
    def validate_all(self) -> bool:
        """
        Run all validation checks.
        
        Returns:
            True if validation passes, False otherwise
        """
        self.errors = []
        
        # Check for unsupported resources
        if not self._validate_supported_resources():
            return False
        
        # Get user-defined resources
        user_resources = self._get_user_resources()
        if not user_resources:
            self.errors.append("No user resources found in configuration")
            return False
        
        # Validate each resource
        for resource in user_resources:
            if not self._validate_resource(resource):
                return False
        
        return len(self.errors) == 0
    
    def _get_user_resources(self) -> Set:
        """Get user-defined resources, excluding Dynaconf parameters."""
        all_keys = OrderedSet([*self.settings])
        return all_keys - defaults.DEFAULT_PARAMTERS
    
    def _validate_supported_resources(self) -> bool:
        """Check if all resources are supported."""
        user_resources = self._get_user_resources()
        unsupported = (
            {*user_resources} - defaults.DEFAULT_PARAMTERS
        ) - defaults.SUPP_RES
        
        if unsupported:
            self.errors.append(
                f"Unsupported resources found: {', '.join(unsupported)}"
            )
            return False
        return True
    
    def _validate_resource(self, resource_type: str) -> bool:
        """
        Validate a specific resource type.
        
        Args:
            resource_type: Type of resource to validate
            
        Returns:
            True if valid, False otherwise
        """
        if resource_type not in self.settings:
            return True
        
        for resource_id, config in self.settings[resource_type].items():
            if not self._validate_resource_config(
                resource_type, resource_id, config
            ):
                return False
        
        return True
    
    def _validate_resource_config(
        self,
        resource_type: str,
        resource_id: str,
        config: DynaBox
    ) -> bool:
        """
        Validate a specific resource configuration.
        
        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check if config is a proper dictionary
        if not isinstance(config, DynaBox):
            self.errors.append(
                f"Missing subconfig for resource '{resource_id}' in '{resource_type}'"
            )
            return False
        
        # Validate required attributes
        if not config.get(constants.ATTR_NAME):
            self.errors.append(
                f"Missing 'name' attribute in resource '{resource_id}'"
            )
            return False
        
        if not config.get(constants.ATTR_ACTION):
            self.errors.append(
                f"Missing 'action' attribute in resource '{resource_id}'"
            )
            return False
        
        # Validate attributes based on resource type
        if not self._validate_attributes(resource_type, resource_id, config):
            return False
        
        # Validate action values
        if not self._validate_actions(resource_type, resource_id, config):
            return False
        
        return True
    
    def _validate_attributes(
        self,
        resource_type: str,
        resource_id: str,
        config: DynaBox
    ) -> bool:
        """
        Validate that only supported attributes are present.
        
        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        user_attrs = OrderedSet(config.keys()) - defaults.RES_ATTRIBUTES
        
        # Get allowed attributes based on resource type
        allowed_attrs_map = {
            constants.RESOURCE_SERVICE: defaults.SRV_ATTRIBUTES,
            constants.RESOURCE_DIRECTORY: defaults.DIR_ATTRIBUTES,
            constants.RESOURCE_FILE: defaults.FILE_ATTRIBUTES,
        }
        
        allowed = allowed_attrs_map.get(
            resource_type.upper(),
            defaults.RES_ATTRIBUTES
        )
        
        unsupported = user_attrs - allowed
        if unsupported:
            self.errors.append(
                f"Unsupported attributes in '{resource_id}': "
                f"{', '.join(unsupported)}"
            )
            return False
        
        return True
    
    def _validate_actions(
        self,
        resource_type: str,
        resource_id: str,
        config: DynaBox
    ) -> bool:
        """
        Validate that action values are supported.
        
        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        actions = config.get(constants.ATTR_ACTION, [])
        
        # Define allowed actions per resource type
        allowed_actions_map = {
            constants.RESOURCE_SERVICE: (
                defaults.SERVICE_SETUP_ACTIONS.union(defaults.SERVICE_OP_ACTIONS)
            ),
            constants.RESOURCE_FILE: defaults.DIR_FILE_ACTIONS,
            constants.RESOURCE_DIRECTORY: defaults.DIR_FILE_ACTIONS,
            constants.RESOURCE_FIREWALL: defaults.FIREWALL_ACTIONS,
        }
        
        allowed = allowed_actions_map.get(resource_type.upper(), OrderedSet())
        
        for action in actions:
            if action not in allowed:
                self.errors.append(
                    f"Unsupported action '{action}' in resource '{resource_id}'"
                )
                return False
        
        return True
    
    def get_errors(self) -> List[str]:
        """Get list of validation errors."""
        return self.errors
    
    def log_errors(self):
        """Log all validation errors."""
        for error in self.errors:
            logging.warning(f"[{self.recipe_name}] {error}")
