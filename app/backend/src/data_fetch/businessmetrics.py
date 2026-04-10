import asyncio
import pandas as pd
from backend.src.utils.app_logger import logger
#Capacity Billed Hour Calculation
def get_capacity_billed_hours(data_framed_ip:pd.DataFrame, user_query_ip:str):
    """This function calculates the capacity billed hours using target billed hours and AttendaceCapacityForWastage"""
    logger.info("Initalising Capacity Billed Hours Calculation...")
    target_billed_hours_map={"Discipline Head":0, 
                             "Discipline Lead":0, 
                             "Manager":0, 
                             "Senior Engineer":11.5, 
                             "Engineer":9, 
                             "Graduate Engineering Trainee":6.5
                             }
    try:
        data_framed_ip["cTarget_Billed_Hours"]=data_framed_ip["sRole"].map(target_billed_hours_map).fillna(0)
        data_framed_ip["cBilled_Hour_Capacity"]=(
            data_framed_ip["cTarget_Billed_Hours"]*pd.to_numeric(data_framed_ip["sAttendanceCapacityForWastage"], errors="coerce").fillna(0)
            )
        Cumulative_Billed_Hour_Capacity=round(float(data_framed_ip["cBilled_Hour_Capacity"].sum()),2)
        logger.info("Capacity Billed Hours calculated Successfully...")
        return Cumulative_Billed_Hour_Capacity
    except Exception as e:
        logger.exception("Error in calculating capacity billed hour")
        return ("ERROR MESSAGE:Error in calculating capacity billed hours")

def get_nps_score(data_framed_ip:pd.DataFrame):
    """This function calculates the NPS score for the given data"""
    logger.info("Initalising NPS Score Calculation...")
    NPS_score_map={"PROMOTER":100, "NEUTRAL":50, "DETRACTOR":0}
    try:
        NPS_rating=data_framed_ip["sNps"].str.strip().str.upper().map(NPS_score_map).fillna(0)
        Cumulative_NPS_score=round(float(NPS_rating.mean()),2)
        logger.info("NPS rating calculated Successfully...")
        return Cumulative_NPS_score
    except Exception as e:
        logger.exception("Error in calculating NPS rating")
        return ("ERROR MESSAGE:Error in calculating NPS rating")

def get_internal_utilization(data_framed_ip:pd.DataFrame):
    """This function calculates the Internal Utilization"""
    logger.info("Initialising Internal Utilization Calculation...")
    try:
        data_framed_ip["cBilled_Hour_Capacity"]=data_framed_ip["sAttendanceCapacityForWastage"]*data_framed_ip["cTarget_Billed_Hours"]
        total_billed_hours=data_framed_ip.loc[data_framed_ip["sClientName"].fillna(" ").str.strip().str.upper()!="ENVENTURE", "sBilledHours"].sum()
        total_billed_hours_capacity=data_framed_ip.loc[~data_framed_ip["sRole"].fillna("").str.strip().str.upper().isin(["MANAGER","DISCIPLINE HEAD","DISCIPLINE LEAD"]), "cBilled_Hour_Capacity"].sum()
        cumulative_Utilization_Internal=round(float((total_billed_hours/total_billed_hours_capacity)*100),2)
        logger.info("Internal Utilization calculated successfully...")
        return cumulative_Utilization_Internal
    except Exception as e:
        logger.exception("Error in calculating Internal Utilization")
        # raise
        return ("ERROR MESSAGE:Error in calculating Internal Utilization")
    


