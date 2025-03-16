import hashlib
import json
import time
from datetime import datetime
import os
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto.encryption import encrypt_data, decrypt_data
from utils.logger import get_logger

logger = get_logger(__name__)

class Block:
    def __init__(self, index, timestamp, data, previous_hash, difficulty=4):
        """
        Initialize a new block in the blockchain.
        
        Args:
            index (int): Position of the block in the chain
            timestamp (float): Time when the block was created
            data (dict): Content of the block (post data, encrypted)
            previous_hash (str): Hash of the previous block
            difficulty (int): Mining difficulty (default: 4)
        """
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.difficulty = difficulty
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """Calculate the hash of the block."""
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self):
        """
        Mine the block by finding a hash with the required number of leading zeros
        based on the difficulty.
        """
        target = "0" * self.difficulty
        
        logger.info(f"Mining block {self.index} with difficulty {self.difficulty}...")
        
        while self.hash[:self.difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
            
            # Log progress every 10000 attempts
            if self.nonce % 10000 == 0:
                logger.debug(f"Mining attempt {self.nonce}, current hash: {self.hash[:10]}...")
        
        logger.info(f"Block {self.index} mined successfully with hash {self.hash}")
        return self.hash
    
    def to_dict(self):
        """Convert block to dictionary for serialization."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "difficulty": self.difficulty,
            "nonce": self.nonce,
            "hash": self.hash
        }
    
    @classmethod
    def from_dict(cls, block_dict):
        """Create a Block instance from a dictionary."""
        block = cls(
            block_dict["index"],
            block_dict["timestamp"],
            block_dict["data"],
            block_dict["previous_hash"],
            block_dict["difficulty"]
        )
        block.nonce = block_dict["nonce"]
        block.hash = block_dict["hash"]
        return block


class Blockchain:
    def __init__(self, user_id, encryption_key, difficulty=4):
        """
        Initialize a new blockchain.
        
        Args:
            user_id (str): Unique identifier for the blockchain owner
            encryption_key (bytes): Key used to encrypt/decrypt block data
            difficulty (int): Mining difficulty (default: 4)
        """
        self.user_id = user_id
        self.encryption_key = encryption_key
        self.difficulty = difficulty
        self.chain = []
        self.pending_data = []
        
        # Create the genesis block
        logger.info(f"Creating genesis block for user {user_id}")
        self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create the first block in the chain (genesis block)."""
        genesis_data = {
            "type": "genesis",
            "message": encrypt_data(f"Genesis Block for user {self.user_id}", self.encryption_key),
            "timestamp": time.time()
        }
        
        genesis_block = Block(0, time.time(), genesis_data, "0", self.difficulty)
        genesis_block.mine_block()
        self.chain.append(genesis_block)
        
        logger.info("Genesis block created successfully")
    
    def get_latest_block(self):
        """Return the most recent block in the chain."""
        return self.chain[-1]
    
    def add_data_to_pending(self, data_type, content, metadata=None):
        """
        Add data to pending transactions to be included in the next block.
        
        Args:
            data_type (str): Type of data (post, comment, like, etc.)
            content (str): Content of the post/comment
            metadata (dict): Additional metadata for the data
        """
        if metadata is None:
            metadata = {}
        
        encrypted_content = encrypt_data(content, self.encryption_key)
        
        data = {
            "type": data_type,
            "content": encrypted_content,
            "author": self.user_id,
            "timestamp": time.time(),
            "metadata": metadata
        }
        
        self.pending_data.append(data)
        logger.info(f"Added new {data_type} to pending data")
        return data
    
    def mine_pending_data(self):
        """
        Create a new block with all pending data and add it to the chain.
        Returns the new block.
        """
        if not self.pending_data:
            logger.warning("No pending data to mine")
            return None
        
        latest_block = self.get_latest_block()
        new_block = Block(
            latest_block.index + 1,
            time.time(),
            self.pending_data,
            latest_block.hash,
            self.difficulty
        )
        
        new_block.mine_block()
        self.chain.append(new_block)
        
        # Clear pending data after mining
        self.pending_data = []
        
        logger.info(f"New block mined and added to the chain: {new_block.hash}")
        return new_block
    
    def is_chain_valid(self):
        """
        Validate the integrity of the blockchain.
        Returns True if valid, False otherwise.
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Verify hash
            if current_block.hash != current_block.calculate_hash():
                logger.warning(f"Invalid hash in block {current_block.index}")
                return False
            
            # Verify previous hash reference
            if current_block.previous_hash != previous_block.hash:
                logger.warning(f"Invalid previous hash reference in block {current_block.index}")
                return False
            
            # Verify the block is properly mined
            target = "0" * current_block.difficulty
            if current_block.hash[:current_block.difficulty] != target:
                logger.warning(f"Block {current_block.index} not properly mined")
                return False
        
        logger.info("Blockchain validated successfully")
        return True
    
    def validate_chain(self):
        """
        Alias for is_chain_valid() for API compatibility.
        """
        return self.is_chain_valid()
    
    def get_data_by_type(self, data_type):
        """
        Retrieve all data of a specific type from the blockchain.
        
        Args:
            data_type (str): Type of data to retrieve (post, comment, like, etc.)
            
        Returns:
            list: All data entries of the specified type
        """
        result = []
        
        for block in self.chain[1:]:  # Skip genesis block
            for data in block.data:
                if data["type"] == data_type:
                    # Decrypt the content
                    try:
                        decrypted_content = decrypt_data(data["content"], self.encryption_key)
                        data_copy = data.copy()
                        data_copy["content"] = decrypted_content
                        result.append(data_copy)
                    except Exception as e:
                        logger.error(f"Failed to decrypt data in block {block.index}: {str(e)}")
        
        return result
    
    def get_block_by_index(self, index):
        """Get a block by its index."""
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None
    
    def get_block_by_hash(self, hash_value):
        """Get a block by its hash."""
        for block in self.chain:
            if block.hash == hash_value:
                return block
        return None
    
    def export_chain(self, output_path):
        """
        Export the blockchain to a JSON file.
        
        Args:
            output_path (str): Path to save the exported chain
        """
        chain_data = [block.to_dict() for block in self.chain]
        
        try:
            with open(output_path, 'w') as f:
                json.dump(chain_data, f, indent=4)
            
            logger.info(f"Blockchain exported successfully to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export blockchain: {str(e)}")
            return False
    
    @classmethod
    def import_chain(cls, user_id, encryption_key, input_path, difficulty=4):
        """
        Import a blockchain from a JSON file.
        
        Args:
            user_id (str): User ID to associate with the imported chain
            encryption_key (bytes): Key to decrypt the data
            input_path (str): Path to the JSON file
            difficulty (int): Mining difficulty
            
        Returns:
            Blockchain: A new blockchain instance with the imported data
        """
        try:
            with open(input_path, 'r') as f:
                chain_data = json.load(f)
            
            blockchain = cls(user_id, encryption_key, difficulty)
            blockchain.chain = []  # Clear the genesis block
            
            for block_dict in chain_data:
                block = Block.from_dict(block_dict)
                blockchain.chain.append(block)
            
            logger.info(f"Blockchain imported successfully from {input_path}")
            
            # Validate the imported chain
            if not blockchain.is_chain_valid():
                logger.error("Imported blockchain is invalid")
                return None
            
            return blockchain
        except Exception as e:
            logger.error(f"Failed to import blockchain: {str(e)}")
            return None
    
    def set_difficulty(self, new_difficulty):
        """
        Change the mining difficulty.
        
        Args:
            new_difficulty (int): New difficulty level
        """
        if new_difficulty < 1:
            logger.warning("Difficulty cannot be less than 1, setting to 1")
            new_difficulty = 1
        
        self.difficulty = new_difficulty
        logger.info(f"Mining difficulty changed to {new_difficulty}")
