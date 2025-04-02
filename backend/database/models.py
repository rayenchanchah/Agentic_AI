from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    industry = Column(String)
    company_size = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    members = relationship("TeamMember", back_populates="team")
    analyses = relationship("Analysis", back_populates="team")

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    role = Column(String)
    responsibilities = Column(JSON)
    experience_level = Column(String)
    department = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="members")

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    impact_summary = Column(JSON)
    recommendations = Column(JSON)
    risk_assessment = Column(JSON)
    upskilling_opportunities = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="analyses") 