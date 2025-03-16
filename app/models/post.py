import os
import json
import time
import uuid
from datetime import datetime
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto.encryption import encrypt_data, decrypt_data, sign_data, verify_signature
from utils.logger import get_logger

logger = get_logger(__name__)

class Post:
    """Model for posts in BlockJournal."""
    
    def __init__(self, author_id, content, post_id=None, post_type="post"):
        """
        Initialize a new post.
        
        Args:
            author_id (str): User ID of the author
            content (str): Content of the post
            post_id (str, optional): Unique identifier for the post
            post_type (str): Type of post (post, comment, reaction, etc.)
        """
        self.post_id = post_id or str(uuid.uuid4())
        self.author_id = author_id
        self.content = content
        self.post_type = post_type
        self.created_at = int(time.time())
        self.modified_at = int(time.time())
        self.tags = []
        self.mentions = []
        self.attachments = []
        self.metadata = {}
        self.signature = None
        
        logger.debug(f"Post created: {self.post_id} by {author_id}")
    
    def add_tag(self, tag):
        """
        Add a tag to the post.
        
        Args:
            tag (str): Tag to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        if tag and tag not in self.tags:
            self.tags.append(tag)
            return True
        return False
    
    def add_mention(self, user_id):
        """
        Add a user mention to the post.
        
        Args:
            user_id (str): User ID to mention
            
        Returns:
            bool: True if successful, False otherwise
        """
        if user_id and user_id not in self.mentions:
            self.mentions.append(user_id)
            return True
        return False
    
    def add_attachment(self, attachment_data):
        """
        Add an attachment to the post.
        
        Args:
            attachment_data (dict): Attachment information
                - type: Type of attachment (image, video, file, etc.)
                - data: Data for the attachment (encrypted)
                - metadata: Additional information about the attachment
            
        Returns:
            bool: True if successful, False otherwise
        """
        if attachment_data and "type" in attachment_data and "data" in attachment_data:
            self.attachments.append(attachment_data)
            return True
        return False
    
    def update_content(self, new_content):
        """
        Update the post content.
        
        Args:
            new_content (str): New content for the post
            
        Returns:
            bool: True if successful, False otherwise
        """
        if new_content:
            self.content = new_content
            self.modified_at = int(time.time())
            # Reset signature since content changed
            self.signature = None
            return True
        return False
    
    def sign(self, signing_key):
        """
        Sign the post with the author's signing key.
        
        Args:
            signing_key (bytes): Author's signing key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a signature of the key content
            to_sign = {
                "post_id": self.post_id,
                "author_id": self.author_id,
                "content": self.content,
                "created_at": self.created_at,
                "modified_at": self.modified_at
            }
            
            self.signature = sign_data(to_sign, signing_key)
            logger.debug(f"Post {self.post_id} signed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to sign post: {str(e)}")
            return False
    
    def verify(self, verify_key):
        """
        Verify the post's signature.
        
        Args:
            verify_key (bytes): Author's verification key
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        if not self.signature:
            logger.warning(f"Post {self.post_id} has no signature to verify")
            return False
        
        try:
            # Recreate the signed data
            to_verify = {
                "post_id": self.post_id,
                "author_id": self.author_id,
                "content": self.content,
                "created_at": self.created_at,
                "modified_at": self.modified_at
            }
            
            result = verify_signature(to_verify, self.signature, verify_key)
            if result:
                logger.debug(f"Post {self.post_id} signature verified")
            else:
                logger.warning(f"Post {self.post_id} signature verification failed")
            
            return result
        except Exception as e:
            logger.error(f"Signature verification error: {str(e)}")
            return False
    
    def to_dict(self):
        """
        Convert post to dictionary for serialization.
        
        Returns:
            dict: Post data as dictionary
        """
        return {
            "post_id": self.post_id,
            "author_id": self.author_id,
            "content": self.content,
            "post_type": self.post_type,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "tags": self.tags,
            "mentions": self.mentions,
            "attachments": self.attachments,
            "metadata": self.metadata,
            "signature": self.signature
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a Post instance from a dictionary.
        
        Args:
            data (dict): Post data
            
        Returns:
            Post: Post object
        """
        post = cls(
            data["author_id"],
            data["content"],
            data["post_id"],
            data["post_type"]
        )
        
        post.created_at = data["created_at"]
        post.modified_at = data["modified_at"]
        post.tags = data["tags"]
        post.mentions = data["mentions"]
        post.attachments = data["attachments"]
        post.metadata = data["metadata"]
        post.signature = data["signature"]
        
        return post
    
    def encrypt_content(self, encryption_key):
        """
        Encrypt the post content.
        
        Args:
            encryption_key (bytes): Key to encrypt the content
            
        Returns:
            dict: Dictionary with encrypted content
        """
        try:
            encrypted_post = self.to_dict()
            
            # Encrypt the content
            encrypted_post["content"] = encrypt_data(self.content, encryption_key)
            
            # Encrypt attachments data
            for i, attachment in enumerate(self.attachments):
                if "data" in attachment:
                    encrypted_post["attachments"][i]["data"] = encrypt_data(
                        attachment["data"], encryption_key
                    )
            
            logger.debug(f"Post {self.post_id} content encrypted")
            return encrypted_post
        except Exception as e:
            logger.error(f"Failed to encrypt post content: {str(e)}")
            return None
    
    @classmethod
    def decrypt_content(cls, encrypted_post, encryption_key):
        """
        Decrypt an encrypted post.
        
        Args:
            encrypted_post (dict): Encrypted post data
            encryption_key (bytes): Key to decrypt the content
            
        Returns:
            Post: Post object with decrypted content
        """
        try:
            post_data = encrypted_post.copy()
            
            # Decrypt the content
            post_data["content"] = decrypt_data(encrypted_post["content"], encryption_key)
            
            # Decrypt attachments
            for i, attachment in enumerate(post_data["attachments"]):
                if "data" in attachment:
                    post_data["attachments"][i]["data"] = decrypt_data(
                        attachment["data"], encryption_key
                    )
            
            logger.debug(f"Post {encrypted_post['post_id']} content decrypted")
            return cls.from_dict(post_data)
        except Exception as e:
            logger.error(f"Failed to decrypt post content: {str(e)}")
            return None


class Comment(Post):
    """Model for comments in BlockJournal."""
    
    def __init__(self, author_id, content, parent_id, post_id=None):
        """
        Initialize a new comment.
        
        Args:
            author_id (str): User ID of the author
            content (str): Content of the comment
            parent_id (str): ID of the parent post or comment
            post_id (str, optional): Unique identifier for the comment
        """
        super().__init__(author_id, content, post_id, "comment")
        self.parent_id = parent_id
        
        logger.debug(f"Comment created: {self.post_id} by {author_id} on {parent_id}")
    
    def to_dict(self):
        """
        Convert comment to dictionary for serialization.
        
        Returns:
            dict: Comment data as dictionary
        """
        comment_dict = super().to_dict()
        comment_dict["parent_id"] = self.parent_id
        return comment_dict
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a Comment instance from a dictionary.
        
        Args:
            data (dict): Comment data
            
        Returns:
            Comment: Comment object
        """
        comment = cls(
            data["author_id"],
            data["content"],
            data["parent_id"],
            data["post_id"]
        )
        
        comment.created_at = data["created_at"]
        comment.modified_at = data["modified_at"]
        comment.tags = data["tags"]
        comment.mentions = data["mentions"]
        comment.attachments = data["attachments"]
        comment.metadata = data["metadata"]
        comment.signature = data["signature"]
        
        return comment


class Reaction(Post):
    """Model for reactions in BlockJournal."""
    
    def __init__(self, author_id, reaction_type, parent_id, post_id=None):
        """
        Initialize a new reaction.
        
        Args:
            author_id (str): User ID of the author
            reaction_type (str): Type of reaction (like, love, etc.)
            parent_id (str): ID of the parent post or comment
            post_id (str, optional): Unique identifier for the reaction
        """
        super().__init__(author_id, reaction_type, post_id, "reaction")
        self.parent_id = parent_id
        self.reaction_type = reaction_type
        
        logger.debug(f"Reaction created: {self.post_id} by {author_id} on {parent_id}")
    
    def to_dict(self):
        """
        Convert reaction to dictionary for serialization.
        
        Returns:
            dict: Reaction data as dictionary
        """
        reaction_dict = super().to_dict()
        reaction_dict["parent_id"] = self.parent_id
        reaction_dict["reaction_type"] = self.reaction_type
        return reaction_dict
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a Reaction instance from a dictionary.
        
        Args:
            data (dict): Reaction data
            
        Returns:
            Reaction: Reaction object
        """
        reaction = cls(
            data["author_id"],
            data["reaction_type"],
            data["parent_id"],
            data["post_id"]
        )
        
        reaction.created_at = data["created_at"]
        reaction.modified_at = data["modified_at"]
        reaction.tags = data["tags"]
        reaction.mentions = data["mentions"]
        reaction.attachments = data["attachments"]
        reaction.metadata = data["metadata"]
        reaction.signature = data["signature"]
        
        return reaction
