import os
import json
import shutil
import time
from datetime import datetime
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger
from blockchain.blockchain import Block, Blockchain

logger = get_logger(__name__)

class BlockchainStorage:
    """Interface for storing and retrieving blockchain data."""
    
    def __init__(self, data_dir, user_id):
        """
        Initialize the blockchain storage.
        
        Args:
            data_dir (str): Directory to store data
            user_id (str): ID of the user whose data is being stored
        """
        self.data_dir = data_dir
        self.user_id = user_id
        self.user_dir = os.path.join(data_dir, user_id)
        self.blocks_dir = os.path.join(self.user_dir, 'blocks')
        self.index_file = os.path.join(self.user_dir, 'chain_index.json')
        
        # Create directories if they don't exist
        os.makedirs(self.blocks_dir, exist_ok=True)
        
        logger.info(f"Blockchain storage initialized for user {user_id}")
    
    def save_block(self, block):
        """
        Save a block to storage.
        
        Args:
            block (Block): Block to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            block_file = os.path.join(self.blocks_dir, f"{block.index}.json")
            
            with open(block_file, 'w') as f:
                json.dump(block.to_dict(), f, indent=4)
            
            logger.debug(f"Block {block.index} saved to {block_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save block {block.index}: {str(e)}")
            return False
    
    def load_block(self, block_index):
        """
        Load a block from storage.
        
        Args:
            block_index (int): Index of the block to load
            
        Returns:
            Block: Loaded block or None if not found
        """
        try:
            block_file = os.path.join(self.blocks_dir, f"{block_index}.json")
            
            if not os.path.exists(block_file):
                logger.warning(f"Block file {block_file} does not exist")
                return None
            
            with open(block_file, 'r') as f:
                block_data = json.load(f)
            
            block = Block.from_dict(block_data)
            logger.debug(f"Block {block_index} loaded from {block_file}")
            return block
        except Exception as e:
            logger.error(f"Failed to load block {block_index}: {str(e)}")
            return None
    
    def save_chain_index(self, blockchain):
        """
        Save blockchain index information.
        
        Args:
            blockchain (Blockchain): Blockchain to save index for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create index data
            index_data = {
                "user_id": self.user_id,
                "last_updated": int(time.time()),
                "block_count": len(blockchain.chain),
                "latest_block_hash": blockchain.get_latest_block().hash,
                "difficulty": blockchain.difficulty
            }
            
            with open(self.index_file, 'w') as f:
                json.dump(index_data, f, indent=4)
            
            logger.info(f"Chain index saved to {self.index_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save chain index: {str(e)}")
            return False
    
    def load_chain_index(self):
        """
        Load blockchain index information.
        
        Returns:
            dict: Index data or None if not found
        """
        try:
            if not os.path.exists(self.index_file):
                logger.warning(f"Chain index file {self.index_file} does not exist")
                return None
            
            with open(self.index_file, 'r') as f:
                index_data = json.load(f)
            
            logger.info(f"Chain index loaded from {self.index_file}")
            return index_data
        except Exception as e:
            logger.error(f"Failed to load chain index: {str(e)}")
            return None
    
    def save_blockchain(self, blockchain):
        """
        Save the entire blockchain to storage.
        
        Args:
            blockchain (Blockchain): Blockchain to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Save each block
            for block in blockchain.chain:
                self.save_block(block)
            
            # Save the index
            self.save_chain_index(blockchain)
            
            logger.info(f"Blockchain saved for user {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save blockchain: {str(e)}")
            return False
    
    def load_blockchain(self, user_id, encryption_key, difficulty=4):
        """
        Load a blockchain from storage.
        
        Args:
            user_id (str): User ID for the blockchain
            encryption_key (bytes): Key to decrypt block data
            difficulty (int): Mining difficulty
            
        Returns:
            Blockchain: Loaded blockchain or None if not found
        """
        try:
            # Load index data
            index_data = self.load_chain_index()
            
            if not index_data:
                logger.warning(f"No chain index found for user {user_id}")
                return None
            
            # Create a new blockchain
            blockchain = Blockchain(user_id, encryption_key, index_data["difficulty"])
            blockchain.chain = []  # Clear the genesis block that was created automatically
            
            # Load each block
            block_count = index_data["block_count"]
            for i in range(block_count):
                block = self.load_block(i)
                if block:
                    blockchain.chain.append(block)
                else:
                    logger.error(f"Failed to load block {i}, chain may be incomplete")
                    return None
            
            # Verify chain integrity
            if not blockchain.is_chain_valid():
                logger.error(f"Loaded blockchain for user {user_id} is invalid")
                return None
            
            logger.info(f"Blockchain loaded for user {user_id} with {block_count} blocks")
            return blockchain
        except Exception as e:
            logger.error(f"Failed to load blockchain: {str(e)}")
            return None
    
    def create_backup(self, backup_dir=None, timestamp=True):
        """
        Create a backup of the blockchain data.
        
        Args:
            backup_dir (str, optional): Directory to store the backup
            timestamp (bool): Whether to include a timestamp in the backup name
            
        Returns:
            str: Path to the backup directory or None if backup failed
        """
        try:
            # Generate backup path
            if backup_dir is None:
                backup_dir = os.path.join(self.data_dir, 'backups')
            
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_name = self.user_id
            if timestamp:
                backup_name += f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_path = os.path.join(backup_dir, backup_name)
            
            # Copy user directory to backup
            shutil.copytree(self.user_dir, backup_path)
            
            logger.info(f"Blockchain backup created at {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            return None
    
    def restore_from_backup(self, backup_path):
        """
        Restore blockchain data from a backup.
        
        Args:
            backup_path (str): Path to the backup directory
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Backup path {backup_path} does not exist")
                return False
            
            # Remove existing data
            if os.path.exists(self.user_dir):
                shutil.rmtree(self.user_dir)
            
            # Copy backup to user directory
            shutil.copytree(backup_path, self.user_dir)
            
            logger.info(f"Blockchain restored from backup at {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore from backup: {str(e)}")
            return False
    
    def get_chain_stats(self):
        """
        Get statistics about the stored blockchain.
        
        Returns:
            dict: Blockchain statistics
        """
        try:
            stats = {
                "user_id": self.user_id,
                "data_dir": self.data_dir,
                "exists": os.path.exists(self.user_dir)
            }
            
            if not stats["exists"]:
                return stats
            
            # Load index data
            index_data = self.load_chain_index()
            if index_data:
                stats.update(index_data)
            
            # Count files
            stats["block_files"] = len(os.listdir(self.blocks_dir))
            
            # Get total size
            total_size = 0
            for root, dirs, files in os.walk(self.user_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            
            stats["total_size_bytes"] = total_size
            stats["total_size_mb"] = total_size / (1024 * 1024)
            
            logger.info(f"Chain stats retrieved for user {self.user_id}")
            return stats
        except Exception as e:
            logger.error(f"Failed to get chain stats: {str(e)}")
            return {"user_id": self.user_id, "error": str(e)}
    
    def delete_chain(self):
        """
        Delete the entire blockchain from storage.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if os.path.exists(self.user_dir):
                shutil.rmtree(self.user_dir)
                logger.warning(f"Blockchain data deleted for user {self.user_id}")
                return True
            else:
                logger.warning(f"No blockchain data found for user {self.user_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete blockchain data: {str(e)}")
            return False
